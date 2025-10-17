"""
Bot de Telegram con agente inteligente de ventas usando LangChain
Punto de entrada principal del programa
"""
import os
import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
import sys

# Agregar el directorio actual al path para imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.neon import NeonDatabase
from servicio.openai import GroqService
from src.tools import SalesAgent, HybridAssistant

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

# Instancias globales
db: NeonDatabase = None
groq_service: GroqService = None
sales_agent: SalesAgent = None
assistant: HybridAssistant = None


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando /start - Mensaje de bienvenida
    """
    welcome_message = """
🤖 ¡Bienvenido al Asistente Inteligente de Ventas!

Puedo ayudarte con:

📊 **Consultas de Datos:**
• ¿Cuántas facturas tenemos?
• ¿Cuántos clientes únicos hay?
• Muéstrame las últimas 10 ventas
• ¿Quién es el cliente con más ventas?
• Dame estadísticas del mes

💬 **Conversación General:**
• Información sobre productos
• Preguntas frecuentes
• Asistencia general

Solo pregúntame lo que necesites y yo buscaré la información en la base de datos automáticamente.

Comandos disponibles:
/start - Ver este mensaje
/help - Obtener ayuda
/stats - Estadísticas generales
/schema - Ver estructura de la base de datos
"""
    await update.message.reply_text(welcome_message)
    logger.info(f"👤 Usuario {update.effective_user.username} inició el bot")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando /help - Información de ayuda
    """
    help_text = """
🆘 **Ayuda del Bot**

**Ejemplos de preguntas que puedes hacer:**

📈 Estadísticas:
- ¿Cuántas facturas tenemos en total?
- ¿Cuántos clientes únicos hay?
- Dame el total de ventas

👥 Clientes:
- ¿Quién es el cliente con más ventas?
- Lista los últimos 5 clientes
- Busca ventas del usuario [nombre]

📅 Fechas:
- ¿Cuántas ventas hubo hoy?
- Muéstrame ventas de esta semana
- Ventas del último mes

El bot usa inteligencia artificial para entender tu pregunta y generar las consultas SQL necesarias automáticamente.

¡No necesitas saber SQL, solo pregunta en lenguaje natural!
"""
    await update.message.reply_text(help_text)


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando /stats - Muestra estadísticas rápidas
    """
    await update.message.reply_text("📊 Consultando estadísticas...")
    
    try:
        # Usar el SQL Agent para obtener estadísticas
        response = await sales_agent.ask(
            "Dame un resumen completo de estadísticas: total de facturas, total de clientes únicos, "
            "fecha de la primera y última venta. Formatea la respuesta de manera clara."
        )
        await update.message.reply_text(f"📊 **Estadísticas Generales**\n\n{response}")
    except Exception as e:
        logger.error(f"Error al obtener estadísticas: {e}")
        await update.message.reply_text(f"❌ Error al obtener estadísticas: {str(e)}")


async def schema_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando /schema - Muestra la estructura de la base de datos
    """
    try:
        schema_info = sales_agent.get_table_info()
        message = f"🗄️ **Estructura de la Base de Datos:**\n\n```\n{schema_info}\n```"
        await update.message.reply_text(message, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error al obtener schema: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Maneja mensajes de texto del usuario
    """
    user_message = update.message.text
    username = update.effective_user.username or update.effective_user.first_name
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    logger.info(f"📨 Mensaje de {username} ({user_id}): {user_message}")
    
    # Enviar indicador de "escribiendo..."
    await update.message.chat.send_action(action="typing")
    
    try:
        # Usar el asistente híbrido para procesar el mensaje
        response = await assistant.process_message(user_message, username)
        
        # Enviar respuesta (SIN GUARDAR EN BD - SOLO CONSULTAS)
        await update.message.reply_text(response)
        logger.info(f"✅ Respuesta enviada a {username}")
        
    except Exception as e:
        error_msg = f"❌ Lo siento, ocurrió un error al procesar tu mensaje: {str(e)}"
        logger.error(f"Error al procesar mensaje: {e}", exc_info=True)
        await update.message.reply_text(error_msg)


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Maneja errores
    """
    logger.error(f"Error del bot: {context.error}", exc_info=context.error)
    
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "❌ Ocurrió un error inesperado. Por favor, intenta de nuevo más tarde."
        )


async def initialize_services():
    """
    Inicializa todos los servicios necesarios
    """
    global db, groq_service, sales_agent, assistant
    
    logger.info("🚀 Iniciando servicios...")
    
    # 1. Inicializar base de datos
    logger.info("1️⃣ Inicializando base de datos...")
    db = NeonDatabase()
    await db.initialize()
    
    # 2. Inicializar servicio de Groq
    logger.info("2️⃣ Inicializando servicio Groq...")
    groq_service = GroqService()
    
    # 3. Inicializar SQL Agent (se ejecuta en un thread separado para evitar conflictos)
    logger.info("3️⃣ Inicializando SQL Agent con LangChain...")
    loop = asyncio.get_event_loop()
    sales_agent = await loop.run_in_executor(None, SalesAgent)
    
    # 4. Inicializar asistente híbrido
    logger.info("4️⃣ Inicializando asistente híbrido...")
    assistant = HybridAssistant(sales_agent, groq_service)
    
    logger.info("✅ Todos los servicios iniciados correctamente")


async def main():
    """
    Función principal que inicia el bot
    """
    logger.info("=" * 60)
    logger.info("🤖 INICIANDO BOT DE TELEGRAM CON SQL AGENT")
    logger.info("=" * 60)
    
    # Verificar variables de entorno
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        logger.error("❌ TELEGRAM_TOKEN no está configurado")
        return
    
    # Inicializar servicios
    try:
        await initialize_services()
    except Exception as e:
        logger.error(f"❌ Error al inicializar servicios: {e}", exc_info=True)
        return
    
    # Crear aplicación de Telegram
    logger.info("🔧 Configurando handlers del bot...")
    app = Application.builder().token(token).build()
    
    # Registrar comandos
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("schema", schema_command))
    
    # Registrar handler de mensajes
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Registrar handler de errores
    app.add_error_handler(error_handler)
    
    # Iniciar bot
    logger.info("🚀 Bot iniciado y escuchando mensajes...")
    logger.info("Presiona Ctrl+C para detener el bot")
    logger.info("=" * 60)
    
    # Usar initialize y start en lugar de run_polling para evitar conflictos de event loop
    async with app:
        await app.initialize()
        await app.start()
        await app.updater.start_polling(allowed_updates=Update.ALL_TYPES)
        
        # Mantener el bot corriendo
        try:
            await asyncio.Event().wait()
        except (KeyboardInterrupt, SystemExit):
            logger.info("\n👋 Deteniendo bot...")
        finally:
            await app.updater.stop()
            await app.stop()
            await app.shutdown()


if __name__ == "__main__":
    try:
        # Verificar si ya hay un event loop corriendo
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        
        if loop is not None:
            # Si ya hay un loop, usar create_task
            loop.create_task(main())
        else:
            # Si no hay loop, usar asyncio.run
            asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n👋 Bot detenido por el usuario")
    except Exception as e:
        logger.error(f"❌ Error fatal: {e}", exc_info=True)
