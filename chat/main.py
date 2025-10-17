import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import sys
import logging
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from servicio.openai import groq_service
from database.neon import db

load_dotenv()
TOKEN = os.getenv('TOKEN_TELEGRAM')

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

# Diccionario para almacenar el historial de conversación de cada usuario
user_conversations = {}

# Comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or f"user_{user_id}"
    user_conversations[user_id] = []
    await update.message.reply_text(
        f'¡Hola @{username}! Soy un bot de chat con IA. '
        'Puedes hacerme cualquier pregunta y conversaremos.\n\n'
        'Usa /help para ver los comandos disponibles.'
    )

# Comando /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        'Comandos disponibles:\n'
        '/start - Iniciar bot\n'
        '/help - Mostrar ayuda\n'
        '/clear - Limpiar historial de conversación\n\n'
        '💡 Puedes preguntarme sobre las ventas de la empresa:\n'
        '• "¿Cuántas ventas totales tenemos?"\n'
        '• "Muéstrame las últimas ventas"\n'
        '• "¿Quiénes son los mejores clientes?"\n'
        '• "Busca ventas de [producto]"\n'
        '• O cualquier pregunta general y conversaré contigo.'
    )

async def detect_and_handle_sales_query(user_message: str, username: str):
    """
    Detecta si el mensaje es sobre ventas y retorna información relevante de TODA la empresa
    Returns: (is_sales_query: bool, sales_data: dict)
    """
    message_lower = user_message.lower()
    
    # Patrones específicos que realmente indican consulta de ventas
    sales_patterns = [
        # Estadísticas de ventas
        ('venta', 'tenemos'),
        ('venta', 'hay'),
        ('venta', 'total'),
        ('venta', 'cuánta'),
        ('venta', 'cuanta'),
        ('factura', 'tenemos'),
        ('factura', 'total'),
        ('factura', 'cuánta'),
        ('estadística', 'venta'),
        ('estadística', 'empresa'),
        ('resumen', 'venta'),
        
        # Ventas recientes
        ('última', 'venta'),
        ('reciente', 'venta'),
        ('última', 'factura'),
        
        # Top clientes
        ('mejor', 'cliente'),
        ('top', 'cliente'),
        ('cliente', 'compra'),
        
        # Búsquedas
        ('busca', 'venta'),
        ('encuentra', 'venta'),
        ('buscar', 'factura'),
    ]
    
    # Verificar si el mensaje contiene algún patrón específico
    is_sales_query = any(
        word1 in message_lower and word2 in message_lower 
        for word1, word2 in sales_patterns
    )
    
    # También detectar frases muy específicas
    specific_phrases = [
        'cuántas ventas',
        'cuantas ventas',
        'total de ventas',
        'estadísticas de ventas',
        'últimas ventas',
        'ventas recientes',
        'mejores clientes',
        'top clientes',
        'busca ventas',
        'buscar ventas'
    ]
    
    if not is_sales_query:
        is_sales_query = any(phrase in message_lower for phrase in specific_phrases)
    
    if not is_sales_query:
        return False, None
    
    logger.info(f"✅ Patrón de ventas detectado en: {user_message[:50]}")
    sales_data = {}
    
    try:
        # SIEMPRE obtener estadísticas totales de la empresa
        stats = await db.get_total_sales_stats()
        sales_data['stats'] = stats
        
        # Si pregunta por "últimas", "recientes" o similar
        if any(word in message_lower for word in ['última', 'ultimas', 'reciente', 'recientes', 'muestra']):
            recent_sales = await db.get_recent_sales(limit=5)
            sales_data['recent_sales'] = recent_sales
        
        # Si pregunta por clientes o mejores compradores
        if any(word in message_lower for word in ['cliente', 'clientes', 'mejor', 'mejores', 'top']):
            top_customers = await db.get_top_customers(limit=5)
            sales_data['top_customers'] = top_customers
        
        # Si menciona búsqueda o una palabra específica
        if any(word in message_lower for word in ['busca', 'buscar', 'encuentra', 'contiene', 'sobre', 'relacionado']):
            # Palabras a ignorar en la búsqueda
            ignore_words = ['venta', 'ventas', 'factura', 'facturas', 'busca', 'buscar', 'encuentra', 'sobre', 'de', 'la', 'el', 'los', 'las']
            search_words = [word for word in user_message.split() if len(word) > 4 and word.lower() not in ignore_words]
            if search_words:
                keyword = search_words[0]
                search_results = await db.search_all_sales_by_keyword(keyword, limit=5)
                sales_data['search_results'] = search_results
                sales_data['search_keyword'] = keyword
            
    except Exception as e:
        print(f"Error al obtener datos de ventas: {e}")
        import traceback
        traceback.print_exc()
        return is_sales_query, None
    
    return is_sales_query, sales_data

def format_sales_response(sales_data: dict, username: str) -> str:
    """
    Formatea la respuesta con datos de ventas de TODA la empresa de manera conversacional
    """
    response_parts = []
    
    # Estadísticas generales de la empresa
    if sales_data.get('stats'):
        stats = sales_data['stats']
        if stats.get('total_records', 0) > 0:
            response_parts.append(
                f"📊 Estadísticas de la empresa:\n\n"
                f"💰 Total de registros: {stats['total_records']}\n"
                f"🧾 Facturas únicas: {stats['total_invoices']}\n"
                f"👥 Clientes totales: {stats['total_customers']}"
            )
            
            if stats.get('first_sale'):
                response_parts.append(
                    f"📅 Primera venta: {stats['first_sale'].strftime('%d/%m/%Y')}"
                )
            if stats.get('last_sale'):
                response_parts.append(
                    f"📅 Última venta: {stats['last_sale'].strftime('%d/%m/%Y a las %H:%M')}"
                )
        else:
            return f"❌ No hay registros de ventas en el sistema"
    
    # Ventas recientes
    if sales_data.get('recent_sales'):
        recent = sales_data['recent_sales']
        if recent:
            response_parts.append(f"\n📋 Últimas {len(recent)} ventas de la empresa:")
            for i, sale in enumerate(recent[:5], 1):
                username_text = f"@{sale['username']}" if sale.get('username') else "Cliente"
                response_parts.append(
                    f"\n{i}. 🧾 {sale['invoice_number']} - {username_text}\n"
                    f"   💬 {sale['message_text'][:60]}..."
                )
    
    # Top clientes
    if sales_data.get('top_customers'):
        customers = sales_data['top_customers']
        if customers:
            response_parts.append(f"\n👑 Top {len(customers)} clientes:")
            for i, customer in enumerate(customers, 1):
                response_parts.append(
                    f"\n{i}. @{customer['username']}: {customer['total_purchases']} compras "
                    f"({customer['unique_invoices']} facturas únicas)"
                )
    
    # Resultados de búsqueda
    if sales_data.get('search_results'):
        results = sales_data['search_results']
        keyword = sales_data.get('search_keyword', '')
        if results:
            response_parts.append(f"\n🔍 Encontré {len(results)} resultados para '{keyword}':")
            for i, sale in enumerate(results[:5], 1):
                username_text = f"@{sale['username']}" if sale.get('username') else "Cliente"
                response_parts.append(
                    f"\n{i}. 🧾 {sale['invoice_number']} - {username_text}\n"
                    f"   💬 {sale['message_text'][:50]}..."
                )
        else:
            response_parts.append(f"\n❌ No se encontraron resultados para '{keyword}'")
    
    return '\n'.join(response_parts) if response_parts else None

# Comando /ventas para ver estadísticas de ventas
async def sales_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.effective_user.username
    
    if not username:
        await update.message.reply_text(
            '❌ No tienes un username configurado en Telegram.\n'
            'Por favor configura uno en tu perfil de Telegram para ver tus ventas.'
        )
        return
    
    try:
        stats = await db.get_sales_stats_by_username(username)
        
        if stats and stats['total_invoices'] > 0:
            response = f"📊 Estadísticas de ventas para @{username}:\n\n"
            response += f"💰 Total de registros: {stats['total_invoices']}\n"
            response += f"📋 Facturas únicas: {stats['unique_invoice_numbers']}\n"
            
            if stats['first_sale']:
                response += f"📅 Primera venta: {stats['first_sale'].strftime('%Y-%m-%d %H:%M')}\n"
            if stats['last_sale']:
                response += f"📅 Última venta: {stats['last_sale'].strftime('%Y-%m-%d %H:%M')}\n"
            
            await update.message.reply_text(response)
        else:
            await update.message.reply_text(
                f"❌ No se encontraron ventas para el usuario @{username}"
            )
    except Exception as e:
        print(f"Error al obtener estadísticas de ventas: {e}")
        import traceback
        traceback.print_exc()
        await update.message.reply_text("❌ Error al consultar las ventas.")

# Comando /misventas para ver ventas recientes
async def my_sales_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.effective_user.username
    
    if not username:
        await update.message.reply_text(
            '❌ No tienes un username configurado en Telegram.\n'
            'Por favor configura uno en tu perfil de Telegram.'
        )
        return
    
    try:
        sales = await db.get_recent_sales_by_username(username, limit=5)
        
        if sales:
            response = f"📋 Tus últimas {len(sales)} ventas:\n\n"
            for i, sale in enumerate(sales, 1):
                response += f"{i}. 🧾 Factura: {sale['invoice_number']}\n"
                response += f"   💬 Consulta: {sale['message_text'][:60]}...\n"
                if sale.get('created_at'):
                    response += f"   📅 Fecha: {sale['created_at'].strftime('%Y-%m-%d %H:%M')}\n"
                response += "\n"
            
            await update.message.reply_text(response)
        else:
            await update.message.reply_text(
                f"❌ No se encontraron ventas para @{username}"
            )
    except Exception as e:
        print(f"Error al obtener ventas: {e}")
        import traceback
        traceback.print_exc()
        await update.message.reply_text("❌ Error al consultar las ventas.")

# Comando /buscar para buscar ventas por palabra clave
async def search_sales_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.effective_user.username
    
    if not username:
        await update.message.reply_text(
            '❌ No tienes un username configurado en Telegram.\n'
            'Por favor configura uno en tu perfil de Telegram.'
        )
        return
    
    # Obtener la palabra clave del comando
    if not context.args:
        await update.message.reply_text(
            '❌ Por favor especifica una palabra clave.\n'
            'Ejemplo: /buscar producto'
        )
        return
    
    keyword = ' '.join(context.args)
    
    try:
        results = await db.search_sales_by_keyword(username, keyword, limit=5)
        
        if results:
            response = f"🔍 Resultados de búsqueda para '{keyword}':\n\n"
            for i, sale in enumerate(results, 1):
                response += f"{i}. 🧾 Factura: {sale['invoice_number']}\n"
                response += f"   💬 Consulta: {sale['message_text'][:60]}...\n"
                response += f"   📅 Fecha: {sale.get('created_at', 'N/A')}\n\n"
            
            await update.message.reply_text(response)
        else:
            await update.message.reply_text(
                f"❌ No se encontraron ventas con la palabra '{keyword}'"
            )
    except Exception as e:
        print(f"Error al buscar ventas: {e}")
        import traceback
        traceback.print_exc()
        await update.message.reply_text("❌ Error al buscar en las ventas.")

# Comando /clear para limpiar el historial
async def clear_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_conversations[user_id] = []
    await update.message.reply_text('Historial de conversación limpiado. ¡Empecemos de nuevo!')

# Manejador de mensajes de texto
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start_time = datetime.now()
    user_id = update.effective_user.id
    username = update.effective_user.username or f"user_{user_id}"
    user_message = update.message.text
    
    logger.info(f"📥 Mensaje recibido de @{username} (ID: {user_id}): {user_message[:100]}")
    
    # Inicializar historial si no existe
    if user_id not in user_conversations:
        user_conversations[user_id] = []
        logger.debug(f"🆕 Nuevo usuario: @{username}")
    
    # Enviar indicador de "escribiendo..."
    await update.message.chat.send_action(action="typing")
    
    try:
        # Primero detectar si es una consulta sobre ventas
        logger.info(f"🔍 Detectando tipo de consulta...")
        is_sales_query, sales_data = await detect_and_handle_sales_query(user_message, username)
        
        if is_sales_query and sales_data:
            logger.info(f"💰 Consulta de ventas detectada")
            # Si es una consulta de ventas, responder con los datos formateados
            sales_response = format_sales_response(sales_data, username)
            
            if sales_response:
                # Enviar respuesta directa de ventas
                await update.message.reply_text(sales_response)
                
                # Guardar en historial
                user_conversations[user_id].append({"role": "user", "content": user_message})
                user_conversations[user_id].append({"role": "assistant", "content": sales_response})
                
                elapsed_time = (datetime.now() - start_time).total_seconds()
                logger.info(f"✅ Respuesta de ventas enviada en {elapsed_time:.2f}s")
                
                return
        
        # Si no es sobre ventas, proceder con el flujo normal de IA
        logger.info(f"🤖 Procesando con IA...")
        # Buscar contexto de FAQs en la base de datos
        faq_context = await db.get_faq_context(
            username=username,
            question=user_message
        )
        
        # Obtener respuesta del servicio de Groq con contexto de FAQs
        response = await groq_service.get_chat_response(
            user_message, 
            user_conversations[user_id],
            faq_context=faq_context
        )
        
        # Actualizar historial
        user_conversations[user_id].append({"role": "user", "content": user_message})
        user_conversations[user_id].append({"role": "assistant", "content": response})
        
        # Limitar historial a las últimas 20 interacciones (10 pares)
        if len(user_conversations[user_id]) > 20:
            user_conversations[user_id] = user_conversations[user_id][-20:]
        
        # Enviar respuesta
        await update.message.reply_text(response)
        
    except Exception as e:
        print(f"Error al procesar mensaje: {e}")
        import traceback
        traceback.print_exc()
        await update.message.reply_text(
            'Lo siento, ocurrió un error al procesar tu mensaje. '
            'Por favor, intenta de nuevo.'
        )

def main():
    # Crear aplicación
    app = Application.builder().token(TOKEN).build()
    
    # Inicializar base de datos al iniciar
    async def post_init(application: Application):
        await db.initialize()
    
    # Cerrar base de datos al detener
    async def post_shutdown(application: Application):
        await db.close()
    
    app.post_init = post_init
    app.post_shutdown = post_shutdown
    
    # Agregar handlers
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('clear', clear_history))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print('🤖 Bot de chat con IA iniciado...')
    print(f'📊 Usando modelo: {os.getenv("MODEL_ID", "openai/gpt-oss-20b")}')
    print(f'💾 Base de datos: Conectada con tabla invoices')
    print(f'💡 Detección automática de consultas de ventas activada')
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()