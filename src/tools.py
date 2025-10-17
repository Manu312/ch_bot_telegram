"""
Herramientas de LangChain para el agente de ventas
"""
from langchain.agents import create_sql_agent
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI
from langchain.agents.agent_types import AgentType
import os
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)


class SalesAgent:
    """
    Agente inteligente que puede responder preguntas sobre ventas y facturación
    usando LangChain y SQL Agent. Genera consultas SQL dinámicamente.
    """
    
    def __init__(self):
        # Configurar el LLM (usando Groq con OpenAI API compatible)
        self.llm = ChatOpenAI(
            model=os.getenv("MODEL_ID", "llama-3.1-70b-versatile"),
            openai_api_key=os.getenv("GROQ_API_KEY"),
            openai_api_base="https://api.groq.com/openai/v1",
            temperature=0,  # Importante: temperatura 0 para consultas precisas
        )
        
        # Conectar a la base de datos PostgreSQL
        db_url = os.getenv("STR_DB")
        if not db_url:
            raise ValueError("STR_DB no está configurada en las variables de entorno")
        
        # SQLAlchemy necesita postgresql+psycopg2:// en lugar de postgresql://
        if db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
        
        self.db = SQLDatabase.from_uri(db_url)
        
        # Crear el toolkit y el agente con ZERO_SHOT (más compatible con Groq)
        toolkit = SQLDatabaseToolkit(db=self.db, llm=self.llm)
        
        self.agent = create_sql_agent(
            llm=self.llm,
            toolkit=toolkit,
            agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,  # Para ver el proceso de pensamiento del agente
            max_iterations=3,  # Reducido para evitar loops
            max_execution_time=20,  # Timeout de 20 segundos
            handle_parsing_errors=True,
            return_intermediate_steps=False,
        )
        
        # Prompt del sistema mejorado
        self.system_prefix = """
Eres un asistente experto en análisis de ventas y facturación.
Tienes acceso a una base de datos PostgreSQL con una tabla 'invoices' que contiene:
- id: identificador único
- invoice_number: número de factura
- user_id: ID del usuario de Telegram
- username: nombre de usuario
- chat_id: ID del chat
- message_text: texto del mensaje/pregunta
- gpt_response: respuesta generada
- created_at: fecha de creación

IMPORTANTE:
1. Cuando te pregunten por "ventas", refiérete a los registros en la tabla invoices
2. Usa ALWAYS las funciones SQL apropiadas (COUNT, SUM, AVG, etc.)
3. Cuando busques por username, usa LOWER() para comparaciones insensibles a mayúsculas
4. Formatea las fechas de manera legible
5. Si no estás seguro de algo, consulta primero la estructura de la tabla
6. Responde en español de manera clara y profesional
7. Incluye números y estadísticas cuando sea relevante

Ejemplos de preguntas que puedes responder:
- ¿Cuántas facturas tenemos en total?
- ¿Quién es el cliente con más ventas?
- ¿Cuántas ventas se hicieron hoy/esta semana/este mes?
- Lista los últimos 5 clientes
- ¿Cuántos clientes únicos tenemos?
"""
        
    async def ask(self, question: str) -> str:
        """
        Procesa una pregunta en lenguaje natural y devuelve la respuesta
        
        Args:
            question: Pregunta del usuario en lenguaje natural
            
        Returns:
            Respuesta generada por el agente
        """
        try:
            logger.info(f"🤖 SQL Agent procesando pregunta: {question}")
            
            # Intentar primero con consultas directas para preguntas comunes
            # (más rápido y confiable que el agente con Groq)
            simple_answer = await self._try_simple_query(question)
            if simple_answer:
                logger.info(f"✅ Respondido con consulta directa")
                return simple_answer
            
            # Si no es una pregunta simple, usar el agente
            # Construir el prompt completo
            full_prompt = f"{self.system_prefix}\n\nPregunta del usuario: {question}\n\nPor favor responde de manera clara y concisa."
            
            # Ejecutar el agente (síncrono, ya que LangChain tiene problemas con async y Groq)
            import asyncio
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: self.agent.invoke({"input": full_prompt})
            )
            
            # Extraer la respuesta
            answer = response.get("output", "No pude procesar la pregunta.")
            
            logger.info(f"✅ SQL Agent respondió: {answer[:200]}...")
            return answer
            
        except Exception as e:
            logger.error(f"❌ Error en SQL Agent: {e}")
            # Intentar responder con el LLM directamente sin herramientas
            return await self._fallback_response(question)
    
    async def _try_simple_query(self, question: str) -> str:
        """
        Intenta responder preguntas simples con consultas directas
        """
        q_lower = question.lower()
        
        try:
            # Cuántas facturas
            if any(word in q_lower for word in ['cuántas facturas', 'total facturas', 'número de facturas']):
                result = self.db.run("SELECT COUNT(*) as total FROM invoices")
                return f"📊 Tenemos un total de **{result}** facturas registradas en el sistema."
            
            # Cuántos clientes
            if any(word in q_lower for word in ['cuántos clientes', 'clientes únicos', 'total clientes']):
                result = self.db.run("SELECT COUNT(DISTINCT username) as total FROM invoices WHERE username IS NOT NULL")
                return f"👥 Hay **{result}** clientes únicos registrados."
            
            # Últimas ventas
            if 'últimas' in q_lower or 'recientes' in q_lower:
                import re
                match = re.search(r'(\d+)', question)
                limit = int(match.group(1)) if match else 5
                result = self.db.run(f"SELECT invoice_number, username, created_at FROM invoices ORDER BY created_at DESC LIMIT {limit}")
                return f"📋 Las últimas {limit} ventas:\n\n{result}"
            
        except Exception as e:
            logger.debug(f"No se pudo responder con consulta simple: {e}")
        
        return None
    
    async def _fallback_response(self, question: str) -> str:
        """
        Respuesta de fallback cuando el agente falla
        """
        try:
            # Obtener estadísticas básicas
            stats = self.db.run("SELECT COUNT(*) as total, COUNT(DISTINCT username) as clientes FROM invoices")
            
            # Usar el LLM para responder basado en estadísticas
            from langchain.schema import HumanMessage, SystemMessage
            
            messages = [
                SystemMessage(content=f"Eres un asistente de ventas. Estadísticas de la BD: {stats}"),
                HumanMessage(content=question)
            ]
            
            response = await self.llm.ainvoke(messages)
            return response.content
            
        except Exception as e:
            logger.error(f"Error en fallback: {e}")
            return "Lo siento, no pude procesar tu pregunta. Por favor intenta reformularla de manera más simple."
    
    def get_table_info(self) -> str:
        """
        Obtiene información sobre las tablas disponibles
        """
        return self.db.get_table_info()


class HybridAssistant:
    """
    Asistente híbrido que combina:
    1. SQL Agent para consultas de datos dinámicas
    2. GPT conversacional para preguntas generales
    """
    
    def __init__(self, sales_agent: SalesAgent, groq_service):
        self.sales_agent = sales_agent
        self.groq_service = groq_service
        
    async def process_message(self, message: str, username: str = None) -> str:
        """
        Procesa un mensaje decidiendo si usar el SQL Agent o el chat conversacional
        
        Args:
            message: Mensaje del usuario
            username: Username del usuario (opcional)
            
        Returns:
            Respuesta apropiada
        """
        # Keywords que indican una consulta de datos
        data_keywords = [
            'cuántos', 'cuántas', 'total', 'cantidad', 'estadística', 'ventas',
            'facturas', 'clientes', 'último', 'últimas', 'primero', 'promedio',
            'lista', 'muestra', 'busca', 'encuentra', 'mayor', 'menor',
            'suma', 'top', 'ranking', 'comparar', 'mostrar', 'dame'
        ]
        
        message_lower = message.lower()
        is_data_query = any(keyword in message_lower for keyword in data_keywords)
        
        logger.info(f"🔍 Mensaje clasificado como: {'CONSULTA DE DATOS' if is_data_query else 'CONVERSACIÓN'}")
        
        if is_data_query:
            # Usar el SQL Agent para consultas de datos
            return await self.sales_agent.ask(message)
        else:
            # Usar el chat conversacional normal
            return await self.groq_service.get_chat_response(
                user_message=message,
                conversation_history=None,
                faq_context=None
            )
