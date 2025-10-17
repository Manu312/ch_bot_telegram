import os
import asyncpg
import asyncio
from datetime import datetime
from dotenv import load_dotenv
import json
import logging

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

class NeonDatabase:
    def __init__(self):
        self.conn_string = os.environ.get("STR_DB")
        self.pool = None
    
    async def initialize(self):
        """Inicializa el pool de conexiones y crea las tablas"""
        try:
            logger.info("🔌 Intentando conectar a Neon Database...")
            self.pool = await asyncpg.create_pool(self.conn_string, min_size=1, max_size=10)
            logger.info("✅ Base de datos inicializada correctamente")
            print("✓ Base de datos inicializada correctamente")
        except Exception as e:
            logger.error(f"❌ Error al inicializar base de datos: {e}")
            print(f"✗ Error al inicializar base de datos: {e}")
            raise
    async def search_invoices_by_username(self, username: str, limit: int = 10):
        """
        Busca facturas (invoices) por username para encontrar preguntas y respuestas frecuentes
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT 
                    id, 
                    invoice_number,
                    user_id,
                    username,
                    chat_id,
                    message_text,
                    gpt_response,
                    created_at
                FROM invoices
                WHERE LOWER(username) = LOWER($1)
                ORDER BY created_at DESC
                LIMIT $2
            ''', username, limit)
            
            return [dict(row) for row in rows] if rows else []
    
    async def search_similar_questions(self, question: str, limit: int = 5):
        """
        Busca preguntas similares en la tabla invoices usando búsqueda de texto
        """
        async with self.pool.acquire() as conn:
            # Búsqueda usando ILIKE para encontrar texto similar
            search_pattern = f"%{question}%"
            rows = await conn.fetch('''
                SELECT 
                    message_text,
                    gpt_response,
                    username,
                    created_at
                FROM invoices
                WHERE message_text ILIKE $1
                ORDER BY created_at DESC
                LIMIT $2
            ''', search_pattern, limit)
            
            return [dict(row) for row in rows] if rows else []
    
    async def get_faq_context(self, username: str = None, question: str = None):
        """
        Obtiene contexto de FAQs basado en username y/o pregunta similar
        """
        context = {
            'user_history': [],
            'similar_questions': []
        }
        
        # Buscar historial del usuario si se proporciona username
        if username:
            context['user_history'] = await self.search_invoices_by_username(username, limit=5)
        
        # Buscar preguntas similares si se proporciona pregunta
        if question:
            context['similar_questions'] = await self.search_similar_questions(question, limit=3)
        
        return context
    
    async def get_sales_count_by_username(self, username: str):
        """
        Obtiene el número total de ventas (invoices) de un usuario
        """
        async with self.pool.acquire() as conn:
            result = await conn.fetchrow('''
                SELECT 
                    COUNT(*) as total_sales,
                    COUNT(DISTINCT invoice_number) as unique_invoices
                FROM invoices
                WHERE LOWER(username) = LOWER($1)
            ''', username)
            
            return dict(result) if result else {'total_sales': 0, 'unique_invoices': 0}
    
    async def get_sales_stats_by_username(self, username: str):
        """
        Obtiene estadísticas detalladas de ventas de un usuario
        """
        async with self.pool.acquire() as conn:
            stats = await conn.fetchrow('''
                SELECT 
                    COUNT(*) as total_invoices,
                    COUNT(DISTINCT invoice_number) as unique_invoice_numbers,
                    MIN(created_at) as first_sale,
                    MAX(created_at) as last_sale
                FROM invoices
                WHERE LOWER(username) = LOWER($1)
            ''', username)
            
            return dict(stats) if stats else None
    
    async def get_recent_sales_by_username(self, username: str, limit: int = 10):
        """
        Obtiene las ventas más recientes de un usuario
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT 
                    invoice_number,
                    message_text,
                    gpt_response,
                    created_at
                FROM invoices
                WHERE LOWER(username) = LOWER($1)
                ORDER BY created_at DESC
                LIMIT $2
            ''', username, limit)
            
            return [dict(row) for row in rows] if rows else []
    
    async def search_sales_by_keyword(self, username: str, keyword: str, limit: int = 10):
        """
        Busca ventas de un usuario que contengan una palabra clave específica
        """
        async with self.pool.acquire() as conn:
            search_pattern = f"%{keyword}%"
            rows = await conn.fetch('''
                SELECT 
                    invoice_number,
                    message_text,
                    gpt_response,
                    created_at
                FROM invoices
                WHERE LOWER(username) = LOWER($1)
                  AND (message_text ILIKE $2 OR gpt_response ILIKE $2)
                ORDER BY created_at DESC
                LIMIT $3
            ''', username, search_pattern, limit)
            
            return [dict(row) for row in rows] if rows else []
    
    async def get_all_sales_summary(self):
        """
        Obtiene un resumen de todas las ventas en el sistema
        """
        async with self.pool.acquire() as conn:
            result = await conn.fetchrow('''
                SELECT 
                    COUNT(*) as total_invoices,
                    COUNT(DISTINCT username) as total_users,
                    COUNT(DISTINCT invoice_number) as unique_invoices
                FROM invoices
            ''')
            
            return dict(result) if result else None
    
    async def get_total_sales_stats(self):
        """
        Obtiene estadísticas completas de TODAS las ventas de la empresa
        """
        async with self.pool.acquire() as conn:
            stats = await conn.fetchrow('''
                SELECT 
                    COUNT(*) as total_records,
                    COUNT(DISTINCT invoice_number) as total_invoices,
                    COUNT(DISTINCT username) as total_customers,
                    MIN(created_at) as first_sale,
                    MAX(created_at) as last_sale
                FROM invoices
            ''')
            
            return dict(stats) if stats else None
    
    async def get_recent_sales(self, limit: int = 10):
        """
        Obtiene las ventas más recientes de TODA la empresa
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT 
                    invoice_number,
                    username,
                    message_text,
                    gpt_response,
                    created_at
                FROM invoices
                ORDER BY created_at DESC
                LIMIT $1
            ''', limit)
            
            return [dict(row) for row in rows] if rows else []
    
    async def search_all_sales_by_keyword(self, keyword: str, limit: int = 10):
        """
        Busca en TODAS las ventas de la empresa que contengan una palabra clave
        """
        async with self.pool.acquire() as conn:
            search_pattern = f"%{keyword}%"
            rows = await conn.fetch('''
                SELECT 
                    invoice_number,
                    username,
                    message_text,
                    gpt_response,
                    created_at
                FROM invoices
                WHERE message_text ILIKE $1 OR gpt_response ILIKE $1 OR invoice_number ILIKE $1
                ORDER BY created_at DESC
                LIMIT $2
            ''', search_pattern, limit)
            
            return [dict(row) for row in rows] if rows else []
    
    async def get_sales_by_date_range(self, start_date: str = None, end_date: str = None, limit: int = 50):
        """
        Obtiene ventas en un rango de fechas
        """
        async with self.pool.acquire() as conn:
            if start_date and end_date:
                rows = await conn.fetch('''
                    SELECT 
                        invoice_number,
                        username,
                        message_text,
                        created_at
                    FROM invoices
                    WHERE created_at::date BETWEEN $1::date AND $2::date
                    ORDER BY created_at DESC
                    LIMIT $3
                ''', start_date, end_date, limit)
            elif start_date:
                rows = await conn.fetch('''
                    SELECT 
                        invoice_number,
                        username,
                        message_text,
                        created_at
                    FROM invoices
                    WHERE created_at::date >= $1::date
                    ORDER BY created_at DESC
                    LIMIT $2
                ''', start_date, limit)
            else:
                rows = await conn.fetch('''
                    SELECT 
                        invoice_number,
                        username,
                        message_text,
                        created_at
                    FROM invoices
                    ORDER BY created_at DESC
                    LIMIT $1
                ''', limit)
            
            return [dict(row) for row in rows] if rows else []
    
    async def get_top_customers(self, limit: int = 10):
        """
        Obtiene los clientes con más ventas
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT 
                    username,
                    COUNT(*) as total_purchases,
                    COUNT(DISTINCT invoice_number) as unique_invoices,
                    MAX(created_at) as last_purchase
                FROM invoices
                WHERE username IS NOT NULL
                GROUP BY username
                ORDER BY total_purchases DESC
                LIMIT $1
            ''', limit)
            
            return [dict(row) for row in rows] if rows else []
    
    async def query_sales_data(self, query_type: str, **kwargs):
        """
        Método unificado para consultar datos de ventas
        
        query_type puede ser:
        - 'total': Estadísticas totales
        - 'recent': Ventas recientes
        - 'search': Búsqueda por palabra clave
        - 'date_range': Ventas en rango de fechas
        - 'top_customers': Mejores clientes
        """
        if query_type == 'total':
            return await self.get_total_sales_stats()
        elif query_type == 'recent':
            limit = kwargs.get('limit', 10)
            return await self.get_recent_sales(limit)
        elif query_type == 'search':
            keyword = kwargs.get('keyword', '')
            limit = kwargs.get('limit', 10)
            return await self.search_all_sales_by_keyword(keyword, limit)
        elif query_type == 'date_range':
            start_date = kwargs.get('start_date')
            end_date = kwargs.get('end_date')
            limit = kwargs.get('limit', 50)
            return await self.get_sales_by_date_range(start_date, end_date, limit)
        elif query_type == 'top_customers':
            limit = kwargs.get('limit', 10)
            return await self.get_top_customers(limit)
        else:
            return None
        
    async def get_bot_conversation_history(self, user_id: int, limit: int = 20):
        """Obtiene el historial de conversación del bot para un usuario"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT role, content, created_at
                FROM bot_conversations
                WHERE user_id = $1
                ORDER BY created_at DESC
                LIMIT $2
            ''', user_id, limit)
            
            # Invertir el orden para tener los mensajes más antiguos primero
            messages = []
            for row in reversed(rows):
                messages.append({
                    "role": row['role'],
                    "content": row['content']
                })
            return messages
    
    async def close(self):
        """Cierra el pool de conexiones"""
        if self.pool:
            await self.pool.close()
            print("✓ Conexión a base de datos cerrada")

# Instancia global de la base de datos
db = NeonDatabase()

async def main():
    """Función de prueba"""
    try:
        await db.initialize()
        print("Successfully connected to Neon database!")
        await db.close()
    except Exception as e:
        print(f"Error connecting to Neon: {e}")

if __name__ == "__main__":
    asyncio.run(main())