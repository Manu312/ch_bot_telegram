# 🤖 Bot de Telegram con SQL Agent - Análisis Inteligente de Ventas

Bot de Telegram que utiliza **LangChain SQL Agent** para responder preguntas sobre ventas y facturación en lenguaje natural. El bot genera consultas SQL dinámicamente sin necesidad de programar cada consulta.

## 🌟 Características Principales

- **SQL Agent con LangChain**: Responde preguntas en lenguaje natural generando consultas SQL automáticamente
- **Asistente Híbrido**: Combina consultas de datos con conversación natural
- **Base de Datos PostgreSQL (Neon)**: Almacenamiento de facturas y conversaciones
- **LLM de Groq**: Procesamiento de lenguaje natural rápido y eficiente

## 🚀 Ejemplos de Preguntas que Puede Responder

### 📊 Estadísticas
```
¿Cuántas facturas tenemos en total?
¿Cuántos clientes únicos hay?
Dame estadísticas generales de ventas
```

### � Clientes
```
¿Quién es el cliente con más ventas?
Lista los últimos 5 clientes
Top 10 de clientes por número de compras
```

### 📅 Consultas Temporales
```
¿Cuántas ventas hubo hoy?
Muéstrame las ventas de esta semana
Ventas del último mes
```

### � Búsquedas
```
Busca facturas que contengan "producto X"
Encuentra ventas del usuario @juan
Dame las últimas 10 facturas
```

## 📦 Instalación

### 1. Clonar y configurar el entorno

```bash
cd ch_bot_telegram
# Instalar dependencias
pip install -r requirements.txt
```

### 2. Configurar variables de entorno

Copia el archivo `.env.example` y configura tus credenciales:

```bash
cp .env.example .env
```

Edita `.env` con tus valores:

```env
TELEGRAM_TOKEN=tu_token_aquí
GROQ_API_KEY=tu_api_key_aquí
MODEL_ID=llama-3.1-70b-versatile
STR_DB=postgresql://usuario:password@host.neon.tech/database?sslmode=require
```

### 3. Configurar la base de datos

Asegúrate de tener una tabla `invoices` en PostgreSQL:

```sql
CREATE TABLE invoices (
    id SERIAL PRIMARY KEY,
    invoice_number VARCHAR(255),
    user_id BIGINT,
    username VARCHAR(255),
    chat_id BIGINT,
    message_text TEXT,
    gpt_response TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_username ON invoices(username);
CREATE INDEX idx_created_at ON invoices(created_at);
```

## 🎯 Uso

### Iniciar el bot

```bash
# Desde la raíz del proyecto - ¡ESTE ES EL PUNTO DE ENTRADA!
python src/main.py
```

### Comandos disponibles en Telegram

- `/start` - Iniciar el bot y ver mensaje de bienvenida
- `/help` - Ver ayuda y ejemplos
- `/stats` - Obtener estadísticas rápidas
- `/schema` - Ver estructura de la base de datos

### Hacer preguntas en lenguaje natural

```
Usuario: ¿Cuántas facturas tenemos?
Bot: Tenemos un total de 1,234 facturas en el sistema.

Usuario: ¿Quién es el cliente con más ventas?
Bot: El cliente con más ventas es @juan con 45 compras.

Usuario: Dame las últimas 5 ventas
Bot: [Lista las últimas 5 ventas con detalles]
```

## 🏗️ Arquitectura

```
src/main.py          # ⭐ PUNTO DE ENTRADA PRINCIPAL
├── src/tools.py     # SQL Agent y Asistente Híbrido con LangChain
├── database/neon.py # Conexión y operaciones de base de datos
└── servicio/openai.py # Servicio de chat conversacional
```

### Componentes Clave

1. **SalesAgent** (`src/tools.py`): 
   - Usa LangChain SQL Agent
   - Genera consultas SQL dinámicamente
   - Ejecuta consultas y formatea respuestas

2. **HybridAssistant** (`src/tools.py`):
   - Clasifica preguntas (datos vs conversación)
   - Redirige a SQL Agent o chat conversacional
   - Combina lo mejor de ambos mundos

3. **Bot Principal** (`src/main.py`):
   - Maneja mensajes de Telegram
   - Inicializa todos los servicios
   - Procesa comandos y consultas

## 🔧 Cómo Funciona el SQL Agent

### El poder de LangChain

En lugar de programar consultas específicas como:
```python
# ❌ Enfoque tradicional - limitado
if "cuántas facturas" in mensaje:
    resultado = db.query("SELECT COUNT(*) FROM invoices")
```

El SQL Agent **genera consultas dinámicamente**:
```python
# ✅ Enfoque con SQL Agent - flexible
resultado = await sales_agent.ask("¿Cuántas facturas tenemos?")
# El agente automáticamente:
# 1. Entiende la pregunta
# 2. Genera: SELECT COUNT(*) FROM invoices
# 3. Ejecuta la consulta
# 4. Formatea la respuesta
```

### Ventajas

✅ **Responde preguntas que no programaste**: El agente adapta las consultas  
✅ **Entiende lenguaje natural**: Sinónimos, contexto, variaciones  
✅ **Aprende del schema**: Se adapta a tu estructura de base de datos  
✅ **Seguro**: LangChain previene SQL injection  
✅ **Escalable**: No necesitas mantener cientos de consultas

## 🛠️ Personalización

### Ajustar el comportamiento del SQL Agent

En `src/tools.py`, modifica los parámetros:

```python
self.agent = create_sql_agent(
    llm=self.llm,
    toolkit=toolkit,
    verbose=True,  # Muestra el proceso de pensamiento
    max_iterations=5,  # Límite de iteraciones
    max_execution_time=30,  # Timeout en segundos
)
```

### Personalizar palabras clave de clasificación

En `src/tools.py`, método `HybridAssistant.process_message()`:

```python
data_keywords = [
    'cuántos', 'total', 'estadística', 'ventas',
    # Agrega tus propias keywords aquí
]
```

## 📊 Ideas para Expandir

### 1. Consultas de Facturación Avanzadas

Agrega estas capacidades al agente (solo configurando el prompt):

```python
# El agente puede responder automáticamente:
"¿Cuál fue el mes con más ventas?"
"Compara las ventas de enero vs febrero"
"¿Qué porcentaje representan las ventas de @juan?"
"Dame el promedio de ventas por cliente"
"¿Cuántos clientes nuevos tuvimos este mes?"
```

### 2. Integrar más tablas

Si tienes tablas de productos, clientes, etc:

```sql
-- El agente automáticamente hará JOINs
CREATE TABLE products (id SERIAL, name VARCHAR, price DECIMAL);
CREATE TABLE customers (id SERIAL, name VARCHAR, email VARCHAR);

-- Ahora puedes preguntar:
"¿Cuál es el producto más vendido?"
"¿Qué clientes no han comprado este mes?"
```

### 3. Visualizaciones

```python
# Integra con matplotlib/plotly
if "gráfico" in pregunta or "visualiza" in pregunta:
    datos = await sales_agent.ask(pregunta)
    generar_grafico(datos)
```

### 4. Alertas automáticas

```python
# Monitoreo automático
async def check_daily_sales():
    resultado = await sales_agent.ask(
        "¿Cuántas ventas tuvimos hoy comparado con el promedio?"
    )
    if es_anomalo(resultado):
        enviar_alerta(resultado)
```

## 🛠️ Troubleshooting

### Error: "Import langchain could not be resolved"

```bash
pip install -r requirements.txt
```

### Error de conexión a la base de datos

Verifica:
1. Variable `STR_DB` correcta en `.env`
2. Tu IP en whitelist de Neon
3. Formato: `postgresql://...?sslmode=require`

### El agente no entiende preguntas

Mejora el `system_prefix` en `src/tools.py` con:
- Ejemplos específicos de tu dominio
- Explicación del schema
- Formato de respuestas deseado

## 📝 Notas Importantes

- **Temperatura 0**: Para consultas SQL precisas y determinísticas
- **Verbose Mode**: Útil para debugging (ver logs)
- **Rate Limits**: Ten en cuenta límites de Groq API
- **Seguridad**: LangChain sanitiza consultas pero revisa los logs

## 🔮 Próximos Pasos

Ideas para mejorar el bot:

- [ ] Caché de consultas frecuentes para velocidad
- [ ] Reportes PDF automáticos
- [ ] Dashboard web con Streamlit
- [ ] Integración con Google Sheets
- [ ] Notificaciones de ventas en tiempo real
- [ ] Análisis predictivo con modelos ML

---

## 💡 Ejemplo Completo de Uso

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Configurar .env
cp .env.example .env
# (editar .env con tus credenciales)

# 3. Iniciar el bot
python src/main.py

# 4. En Telegram, chatear con el bot:
# /start
# ¿Cuántas facturas tenemos?
# ¿Quién es el mejor cliente?
# Dame estadísticas de hoy
```

## Comandos del Bot

- `/start` - Inicia el bot y comienza una nueva conversación
- `/help` - Muestra la ayuda con los comandos disponibles
- `/clear` - Limpia el historial de conversación

## Estructura del Proyecto

```
ch_bot_telegram/
├── chat/
│   └── main.py          # Bot de Telegram principal
├── servicio/
│   └── openai.py        # Servicio de integración con Groq
├── database/
│   └── neon.py          # Conexión a base de datos Neon
├── requirements.txt     # Dependencias del proyecto
├── .env.example         # Ejemplo de variables de entorno
└── README.md           # Este archivo
```

## Modelos Disponibles

Puedes usar diferentes modelos de Groq configurando la variable `MODEL_ID`:

- `llama-3.1-70b-versatile` - Mejor calidad, más lento
- `llama-3.1-8b-instant` - Más rápido, buena calidad
- `mixtral-8x7b-32768` - Contexto muy largo

## Contribuir

Las contribuciones son bienvenidas. Por favor, abre un issue o pull request.

## Licencia

MIT
