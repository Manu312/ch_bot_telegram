from openai import OpenAI
import os
from dotenv import load_dotenv
import logging
from datetime import datetime

load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class GroqService:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.environ.get("GROQ_API_KEY"),
            base_url="https://api.groq.com/openai/v1"
        )
        self.model = os.environ.get("MODEL_ID", "openai/gpt-oss-20b")
        
        # System prompt que define el comportamiento del asistente
        self.system_prompt = """Eres un asistente virtual inteligente de una empresa de ventas. 

Tu rol es ayudar a los usuarios con información sobre:
- Consultas de ventas y estadísticas de la empresa
- Preguntas sobre productos y servicios
- Información general del negocio
- Responder preguntas frecuentes basadas en el historial

Directrices de comportamiento:
1. Sé profesional, amable y conciso
2. Si tienes información de la base de datos en el contexto, úsala para dar respuestas precisas
3. Si no tienes información suficiente, sé honesto y sugiere alternativas
4. Mantén un tono conversacional pero profesional
5. Formatea las respuestas de manera clara y legible
6. No inventes datos - si no sabes algo, dilo claramente

Cuando respondas:
- Usa información del contexto proporcionado cuando esté disponible
- Sé específico y basado en datos reales
- Ofrece ayuda adicional cuando sea apropiado
- Mantén las respuestas relevantes y al punto"""
    
    async def get_chat_response(self, user_message: str, conversation_history: list = None, faq_context: dict = None) -> str:
        """
        Obtiene una respuesta del modelo de Groq
        
        Args:
            user_message: El mensaje del usuario
            conversation_history: Historial de la conversación (opcional)
            faq_context: Contexto de preguntas frecuentes de la base de datos (opcional)
        
        Returns:
            La respuesta del modelo
        """
        start_time = datetime.now()
        logger.info(f"🔵 Nueva consulta LLM iniciada")
        logger.info(f"📝 Mensaje usuario: {user_message[:100]}...")
        
        try:
            # Iniciar con el system prompt
            messages = [{"role": "system", "content": self.system_prompt}]
            logger.debug(f"✅ System prompt agregado")
            
            # Agregar contexto de FAQs si está disponible
            if faq_context:
                context_message = self._build_faq_context_message(faq_context)
                if context_message:
                    messages.append({"role": "system", "content": context_message})
                    logger.info(f"📚 Contexto FAQ agregado: {len(context_message)} caracteres")
            
            # Agregar historial de conversación
            if conversation_history:
                messages.extend(conversation_history)
                logger.info(f"💬 Historial agregado: {len(conversation_history)} mensajes")
            
            # Agregar mensaje actual del usuario
            messages.append({"role": "user", "content": user_message})
            
            logger.info(f"🚀 Enviando {len(messages)} mensajes al LLM (modelo: {self.model})")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.5,
                max_tokens=1024,
            )
            
            response_text = response.choices[0].message.content
            elapsed_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"✅ Respuesta LLM recibida en {elapsed_time:.2f}s")
            logger.info(f"📤 Respuesta ({len(response_text)} caracteres): {response_text[:100]}...")
            
            return response_text
            
        except Exception as e:
            elapsed_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"❌ Error al obtener respuesta de Groq después de {elapsed_time:.2f}s: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return "Lo siento, ocurrió un error al procesar tu mensaje."
    
    def _build_faq_context_message(self, faq_context: dict) -> str:
        """
        Construye un mensaje de contexto basado en FAQs
        """
        context_parts = []
        
        # Agregar historial del usuario
        if faq_context.get('user_history'):
            context_parts.append("Historial previo del usuario:")
            for item in faq_context['user_history'][:3]:  # Limitar a 3 items
                context_parts.append(f"- Pregunta: {item['message_text'][:100]}")
                context_parts.append(f"  Respuesta: {item['gpt_response'][:100]}")
        
        # Agregar preguntas similares
        if faq_context.get('similar_questions'):
            context_parts.append("\nPreguntas similares anteriores:")
            for item in faq_context['similar_questions'][:2]:  # Limitar a 2 items
                context_parts.append(f"- Pregunta: {item['message_text'][:100]}")
                context_parts.append(f"  Respuesta: {item['gpt_response'][:100]}")
        
        if context_parts:
            context_parts.insert(0, "Contexto de preguntas frecuentes:")
            context_parts.append("\nUsa este contexto para dar una respuesta más relevante y consistente.")
            return "\n".join(context_parts)
        
        return ""

# Instancia global del servicio
groq_service = GroqService()
