# 🧪 GUÍA DE PRUEBAS - SOLO CONSULTAS SELECT

## ⚙️ Configuración Inicial

### 1. Verificar que .env esté configurado

```bash
cat .env
```

**Debe mostrar:**
```
TELEGRAM_TOKEN=tu_token_aquí
GROQ_API_KEY=tu_api_key_aquí
MODEL_ID=llama-3.1-70b-versatile
STR_DB=postgresql://usuario:password@host/database
```

---

## 🚀 OPCIÓN 1: Prueba Rápida con Python

### Test Básico del SQL Agent

```bash
python -c "
import asyncio
from dotenv import load_dotenv
from src.tools import SalesAgent

load_dotenv()

async def test():
    print('🤖 Inicializando SQL Agent...')
    agent = SalesAgent()
    print('✅ Agente listo!\n')
    
    # Pregunta de prueba
    pregunta = '¿Cuántas facturas tenemos en total?'
    print(f'❓ Pregunta: {pregunta}')
    print('🤔 Procesando...\n')
    
    respuesta = await agent.ask(pregunta)
    print(f'💬 Respuesta:\n{respuesta}')

asyncio.run(test())
"
```

**Respuesta esperada:**
```
🤖 Inicializando SQL Agent...
✅ Agente listo!

❓ Pregunta: ¿Cuántas facturas tenemos en total?
🤔 Procesando...

💬 Respuesta:
Según la consulta a la base de datos, tenemos un total de 1,234 facturas registradas en el sistema.
```

---

## 🤖 OPCIÓN 2: Probar con Telegram (Modo Completo)

### Iniciar el bot

```bash
python src/main.py
```

**Consola mostrará:**
```
============================================================
🤖 INICIANDO BOT DE TELEGRAM CON SQL AGENT
============================================================
🔌 Intentando conectar a Neon Database...
✅ Base de datos inicializada correctamente
✓ Base de datos inicializada correctamente
3️⃣ Inicializando SQL Agent con LangChain...
✅ Todos los servicios iniciados correctamente
🚀 Bot iniciado y escuchando mensajes...
```

---

## 📋 PREGUNTAS DE PRUEBA Y RESPUESTAS ESPERADAS

### CATEGORÍA 1: Estadísticas Básicas

#### Pregunta 1
```
Usuario: ¿Cuántas facturas tenemos?
```
**Respuesta esperada:**
```
Bot: Según los datos de la base de datos, tenemos un total de [NÚMERO] facturas registradas en el sistema.
```

#### Pregunta 2
```
Usuario: ¿Cuántos clientes únicos hay?
```
**Respuesta esperada:**
```
Bot: En la base de datos hay [NÚMERO] clientes únicos registrados.
```

#### Pregunta 3
```
Usuario: Dame el total de registros
```
**Respuesta esperada:**
```
Bot: El total de registros en la tabla de invoices es [NÚMERO].
```

---

### CATEGORÍA 2: Rankings y Top Clientes

#### Pregunta 4
```
Usuario: ¿Quién es el cliente con más ventas?
```
**Respuesta esperada:**
```
Bot: El cliente con más ventas es @[USERNAME] con [NÚMERO] compras realizadas.
```

#### Pregunta 5
```
Usuario: Dame el top 5 de clientes por número de compras
```
**Respuesta esperada:**
```
Bot: Los 5 clientes con más compras son:
1. @usuario1 - 45 compras
2. @usuario2 - 38 compras
3. @usuario3 - 32 compras
4. @usuario4 - 28 compras
5. @usuario5 - 25 compras
```

#### Pregunta 6
```
Usuario: ¿Qué clientes tienen más de 10 compras?
```
**Respuesta esperada:**
```
Bot: Los clientes con más de 10 compras son:
- @cliente1: 45 compras
- @cliente2: 32 compras
- @cliente3: 18 compras
[...]
```

---

### CATEGORÍA 3: Consultas Temporales

#### Pregunta 7
```
Usuario: ¿Cuántas ventas hubo hoy?
```
**Respuesta esperada:**
```
Bot: Hoy se han registrado [NÚMERO] ventas hasta el momento.
```

#### Pregunta 8
```
Usuario: ¿Cuántas facturas se crearon esta semana?
```
**Respuesta esperada:**
```
Bot: En la semana actual se han creado [NÚMERO] facturas.
```

#### Pregunta 9
```
Usuario: Muéstrame las ventas del último mes
```
**Respuesta esperada:**
```
Bot: En el último mes (desde [FECHA] hasta [FECHA]) se registraron [NÚMERO] ventas.

Resumen:
- Total de facturas: [NÚMERO]
- Clientes únicos: [NÚMERO]
- Promedio diario: [NÚMERO] ventas/día
```

---

### CATEGORÍA 4: Búsquedas Específicas

#### Pregunta 10
```
Usuario: Dame las últimas 10 ventas
```
**Respuesta esperada:**
```
Bot: Las últimas 10 ventas registradas son:

1. Factura #[NUM] - @usuario1 - [FECHA]
2. Factura #[NUM] - @usuario2 - [FECHA]
3. Factura #[NUM] - @usuario3 - [FECHA]
[...]
```

#### Pregunta 11
```
Usuario: Busca ventas del usuario juan
```
**Respuesta esperada:**
```
Bot: El usuario @juan tiene [NÚMERO] ventas registradas:
- Primera venta: [FECHA]
- Última venta: [FECHA]
- Total de facturas: [NÚMERO]
```

#### Pregunta 12
```
Usuario: ¿Cuántas facturas tienen la palabra "producto" en el mensaje?
```
**Respuesta esperada:**
```
Bot: Hay [NÚMERO] facturas que contienen la palabra "producto" en el texto del mensaje.
```

---

### CATEGORÍA 5: Análisis Avanzados

#### Pregunta 13
```
Usuario: ¿Cuál fue la primera venta registrada?
```
**Respuesta esperada:**
```
Bot: La primera venta registrada fue el [FECHA] por el cliente @[USERNAME] con la factura número [NUM].
```

#### Pregunta 14
```
Usuario: ¿Cuál es el promedio de ventas por cliente?
```
**Respuesta esperada:**
```
Bot: El promedio de ventas por cliente es de [NÚMERO] compras por cliente.

Detalles:
- Total de ventas: [NUM]
- Total de clientes: [NUM]
- Promedio: [NUM] ventas/cliente
```

#### Pregunta 15
```
Usuario: Compara las ventas de octubre vs septiembre
```
**Respuesta esperada:**
```
Bot: Comparación de ventas:

Octubre:
- Total de ventas: [NUM]
- Clientes únicos: [NUM]

Septiembre:
- Total de ventas: [NUM]
- Clientes únicos: [NUM]

Diferencia: [+/-NUM] ventas ([+/-]X%)
```

---

### CATEGORÍA 6: Estructura de la BD

#### Pregunta 16 (o comando)
```
Usuario: /schema
```
**Respuesta esperada:**
```
Bot: 🗄️ Estructura de la Base de Datos:

Tabla: invoices
Columnas:
- id (integer)
- invoice_number (character varying)
- user_id (bigint)
- username (character varying)
- chat_id (bigint)
- message_text (text)
- gpt_response (text)
- created_at (timestamp without time zone)
```

---

## 🎯 COMANDOS DEL BOT

### /start
```
Usuario: /start
```
**Respuesta esperada:**
```
🤖 ¡Bienvenido al Asistente Inteligente de Ventas!

Puedo ayudarte con:

📊 Consultas de Datos:
• ¿Cuántas facturas tenemos?
• ¿Cuántos clientes únicos hay?
• Muéstrame las últimas 10 ventas
[...]
```

### /help
```
Usuario: /help
```
**Respuesta esperada:**
```
🆘 Ayuda del Bot

Ejemplos de preguntas que puedes hacer:

📈 Estadísticas:
- ¿Cuántas facturas tenemos en total?
[...]
```

### /stats
```
Usuario: /stats
```
**Respuesta esperada:**
```
📊 Consultando estadísticas...

📊 Estadísticas Generales

Total de facturas: [NUM]
Total de clientes únicos: [NUM]
Primera venta: [FECHA]
Última venta: [FECHA]
```

---

## 🔍 VERIFICACIÓN DE FUNCIONAMIENTO

### ✅ El sistema funciona correctamente si:

1. **Conexión a BD**: El bot se conecta sin errores
2. **SQL Agent**: Genera consultas SQL automáticamente (las verás en logs si `verbose=True`)
3. **Respuestas**: Devuelve datos reales de tu base de datos
4. **Formato**: Las respuestas están bien formateadas y son coherentes
5. **Logs**: En consola ves el proceso del agente

### Ejemplo de logs correctos:
```
📨 Mensaje de usuario123 (12345): ¿Cuántas facturas tenemos?
🔍 Mensaje clasificado como: CONSULTA DE DATOS
🤖 SQL Agent procesando pregunta: ¿Cuántas facturas tenemos?

> Entering new AgentExecutor chain...
Action: sql_db_query
Action Input: SELECT COUNT(*) FROM invoices
Observation: [(1234,)]
Thought: I now know the final answer
Final Answer: Tenemos 1234 facturas en total.

> Finished chain.

✅ SQL Agent respondió: Tenemos 1234 facturas en total...
✅ Respuesta enviada a usuario123
```

---

## ⚠️ POSIBLES PROBLEMAS Y SOLUCIONES

### Problema 1: "Import langchain could not be resolved"
**Solución:**
```bash
pip install -r requirements.txt
```

### Problema 2: "No connection to database"
**Solución:**
Verifica tu `STR_DB` en `.env`:
```bash
echo $STR_DB  # o: grep STR_DB .env
```

### Problema 3: El agente no responde bien
**Solución:**
- Revisa los logs en consola (si `verbose=True`)
- El agente aprende del schema, dale preguntas más claras
- Verifica que tu tabla `invoices` tenga datos

### Problema 4: "Error: sqlalchemy..."
**Solución:**
Asegúrate de que la URL de BD empiece con `postgresql://` y tenga el formato:
```
postgresql://user:pass@host.neon.tech/dbname?sslmode=require
```

---

## 🎉 RESUMEN DE PRUEBA EXITOSA

Si el bot responde correctamente a estas preguntas mínimas, está funcionando:

1. ✅ `¿Cuántas facturas tenemos?` → Devuelve un número
2. ✅ `¿Cuántos clientes únicos hay?` → Devuelve un número
3. ✅ `Dame las últimas 5 ventas` → Lista ventas
4. ✅ `/stats` → Muestra estadísticas generales

---

## 📝 NOTAS IMPORTANTES

- ✅ **Solo consultas SELECT**: No guarda nada en la BD
- ✅ **Datos reales**: Todas las respuestas vienen de tu base de datos
- ✅ **SQL dinámico**: El agente genera las consultas automáticamente
- ✅ **Logs detallados**: Puedes ver en consola qué SQL genera el agente
- ✅ **Seguro**: LangChain previene SQL injection

---

## 🚀 SIGUIENTE PASO

Una vez que confirmes que funciona con estas pruebas:
1. Puedes agregar más tablas a tu BD
2. El agente automáticamente las usará
3. Podrás hacer preguntas más complejas con JOINs
4. Sin programar más consultas manualmente

**¡El SQL Agent se adapta a tu schema automáticamente!**
