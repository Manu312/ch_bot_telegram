# Guía de Implementación del SQL Agent

## 🎯 Ideas para Consultas que NO Necesitas Programar

Con el SQL Agent, estas consultas se generan **automáticamente**:

### 📊 Análisis de Ventas

```
✅ PREGUNTAS QUE EL AGENTE PUEDE RESPONDER AUTOMÁTICAMENTE:

1. Estadísticas Básicas:
   - "¿Cuántas ventas tenemos en total?"
   - "¿Cuál es el promedio de ventas por día?"
   - "¿Cuántas ventas se hicieron esta semana?"
   
2. Top Rankings:
   - "¿Quién es el cliente con más compras?"
   - "Dame el top 10 de clientes por número de ventas"
   - "Lista los 5 productos más vendidos"
   
3. Análisis Temporal:
   - "¿Cuántas ventas hubo en octubre?"
   - "Compara las ventas de hoy vs ayer"
   - "¿Cuál fue el mes con más ventas?"
   - "Dame ventas agrupadas por semana"
   
4. Búsquedas Específicas:
   - "Busca ventas que contengan 'laptop'"
   - "¿Cuántas facturas tienen el texto 'premium'?"
   - "Encuentra todas las ventas del usuario @juan"
   
5. Análisis de Clientes:
   - "¿Cuántos clientes únicos tenemos?"
   - "¿Cuántos clientes nuevos hubo este mes?"
   - "Lista clientes que compraron más de 10 veces"
   - "¿Qué porcentaje de clientes son recurrentes?"
   
6. Distribución de Datos:
   - "¿Cuántas ventas hay por día de la semana?"
   - "¿En qué hora del día hay más ventas?"
   - "Dame la distribución de ventas por mes"
```

## 🚀 Cómo Expandir a Más Tablas

### Escenario: Agregar tabla de Productos

```sql
-- 1. Crear tabla de productos
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    price DECIMAL(10,2),
    category VARCHAR(100),
    stock INT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 2. Crear tabla de líneas de factura
CREATE TABLE invoice_items (
    id SERIAL PRIMARY KEY,
    invoice_number VARCHAR(255),
    product_id INT REFERENCES products(id),
    quantity INT,
    unit_price DECIMAL(10,2),
    total DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT NOW()
);
```

**¡Eso es todo!** El SQL Agent automáticamente podrá responder:

```
✅ PREGUNTAS AUTOMÁTICAS CON MÚLTIPLES TABLAS:

- "¿Cuál es el producto más vendido?"
- "Dame el total de ventas en dinero de este mes"
- "¿Qué categoría genera más ingresos?"
- "Lista productos con bajo stock"
- "¿Cuál es el ticket promedio de compra?"
- "¿Qué productos suele comprar el cliente @juan?"
```

## 🎨 Ejemplo de Flujo Completo

### Pregunta del Usuario:
```
"¿Cuántos clientes compraron más de 5 veces este mes?"
```

### Lo que hace el SQL Agent internamente:

```
1. 🧠 Analiza la pregunta:
   - Necesita: COUNT de clientes
   - Condición: más de 5 ventas
   - Período: este mes
   
2. 📝 Genera la consulta SQL:
   SELECT COUNT(DISTINCT username) as clientes_frecuentes
   FROM invoices
   WHERE created_at >= DATE_TRUNC('month', CURRENT_DATE)
   GROUP BY username
   HAVING COUNT(*) > 5
   
3. ⚡ Ejecuta la consulta
4. 📊 Formatea la respuesta
5. 💬 Devuelve: "Hay 23 clientes que han comprado más de 5 veces este mes"
```

## 🔧 Personalizaciones Útiles

### 1. Agregar Contexto de Negocio

En `src/tools.py`, mejora el `system_prefix`:

```python
self.system_prefix = """
Eres un asistente experto en ventas de [TU EMPRESA].

INFORMACIÓN IMPORTANTE:
- Nuestro objetivo de ventas mensual es 1000 facturas
- Consideramos "cliente frecuente" a quien compra +5 veces/mes
- El ticket promedio objetivo es $50
- Trabajamos de Lunes a Sábado

TABLA invoices:
- invoice_number: ID único de factura
- username: Cliente (puede ser None para ventas en tienda)
- message_text: Descripción o pregunta
- gpt_response: Respuesta del sistema
- created_at: Fecha de la venta

Cuando respondas:
1. Incluye comparaciones con objetivos cuando sea relevante
2. Destaca tendencias importantes
3. Sugiere acciones si detectas algo anormal
4. Usa formato claro con emojis
"""
```

### 2. Respuestas con Formato Mejorado

El agente puede formatear respuestas automáticamente:

```python
# Configurar en src/tools.py
self.system_prefix += """

FORMATO DE RESPUESTAS:
- Usa emojis relevantes (📊 📈 👥 💰)
- Resalta números importantes en **negrita**
- Si hay múltiples resultados, usa listas
- Incluye contexto adicional cuando sea útil

Ejemplo:
"📊 Estadísticas de Octubre:
 • Total de ventas: **1,234** facturas
 • Clientes únicos: **456** personas
 • Crecimiento vs mes anterior: **+15%** 📈"
"""
```

### 3. Validación de Respuestas

Agrega validación para detectar respuestas inusuales:

```python
# En src/tools.py, método ask()
async def ask(self, question: str) -> str:
    try:
        response = await self.agent.ainvoke({"input": full_prompt})
        answer = response.get("output", "No pude procesar la pregunta.")
        
        # Validar respuestas sospechosas
        if "error" in answer.lower() or "no encontré" in answer.lower():
            logger.warning(f"⚠️ Respuesta posiblemente errónea: {answer}")
        
        return answer
    except Exception as e:
        logger.error(f"❌ Error en SQL Agent: {e}")
        return f"Lo siento, ocurrió un error: {str(e)}"
```

## 💡 Mejores Prácticas

### ✅ Hacer:

1. **Empezar simple**: Deja que el agente genere consultas básicas primero
2. **Revisar logs**: Usa `verbose=True` para ver qué consultas genera
3. **Iterar el prompt**: Mejora el `system_prefix` basado en respuestas
4. **Agregar índices**: Optimiza tu BD para consultas frecuentes
5. **Cachear resultados**: Para consultas muy comunes

### ❌ Evitar:

1. **Sobre-explicar**: No des demasiados detalles en el prompt
2. **Forzar sintaxis**: Deja que el agente elija la consulta
3. **Ignorar errores**: Monitorea los logs para detectar problemas
4. **Consultas muy complejas**: Para reports muy complejos, usa funciones programadas

## 🔮 Casos de Uso Avanzados

### 1. Alertas Automáticas

```python
# Crear un worker que revise métricas
async def check_metrics():
    agent = SalesAgent()
    
    # Detectar anomalías
    response = await agent.ask(
        "¿Cuántas ventas tenemos hoy comparado con el promedio de los últimos 7 días?"
    )
    
    # Si es anormal, alertar
    if detectar_anomalia(response):
        enviar_telegram_alerta(response)
```

### 2. Reports Automáticos

```python
async def daily_report():
    agent = SalesAgent()
    
    questions = [
        "¿Cuántas ventas tuvimos ayer?",
        "¿Quién fue el mejor cliente?",
        "¿Cuál fue el ticket promedio?",
    ]
    
    report = "📊 REPORTE DIARIO\n\n"
    for q in questions:
        answer = await agent.ask(q)
        report += f"• {q}\n  {answer}\n\n"
    
    enviar_email(report)
```

### 3. Integración con Dashboard

```python
# Usando Streamlit
import streamlit as st

st.title("Dashboard de Ventas Inteligente")

pregunta = st.text_input("Haz una pregunta sobre ventas:")
if pregunta:
    with st.spinner("Consultando..."):
        respuesta = await agent.ask(pregunta)
        st.success(respuesta)
```

## 📚 Recursos Adicionales

- **LangChain Docs**: https://python.langchain.com/docs/use_cases/sql
- **Groq API**: https://console.groq.com/docs
- **PostgreSQL Patterns**: https://www.postgresql.org/docs/current/tutorial-sql.html

---

**💡 Recuerda**: La magia del SQL Agent es que **NO necesitas anticipar todas las preguntas**. El agente aprende de tu schema y genera las consultas automáticamente.
