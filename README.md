# 🚀 RAC Assistant - Optimización Inteligente de Procesos

## 📋 Descripción

RAC Assistant es una aplicación web avanzada para análisis y optimización de procesos empresariales usando IA. Genera diagramas BPMN 2.0 profesionales y proporciona recomendaciones basadas en metodologías Lean, Six Sigma y Power Platform.

## ✨ Características Principales

- 📂 **Carga inteligente de archivos Excel** con mapeo automático de columnas
- 🎨 **Generador de diagramas BPMN 2.0** compatible con Camunda, Bizagi, etc.
- 🔍 **Análisis avanzado de desperdicios Lean**
- 🧠 **Clasificación automática Six Sigma**
- ⚡ **Recomendaciones de automatización Power Platform**
- 🤖 **Chat inteligente** con experto en procesos
- 📊 **Visualización interactiva** con bpmn-js

## 🏗️ Arquitectura del Proyecto

```
rac-assistant/
├── app.py                      # Aplicación principal
├── config.py                   # Configuración centralizada
├── utils.py                    # Utilidades comunes
├── ui_components.py            # Componentes de UI
├── analysis_models.py          # Modelos de análisis IA
├── gemini_integration.py       # Integración Gemini + BPMN
├── bpmn_advanced.py            # Builder BPMN 2.0 avanzado
└── requirements.txt            # Dependencias
```

## 📦 Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/rac-assistant.git
cd rac-assistant
```

### 2. Crear entorno virtual

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

**requirements.txt:**

```
streamlit>=1.28.0
pandas>=2.0.0
openpyxl>=3.1.0
google-generativeai>=0.3.0
requests>=2.31.0
openai>=1.0.0  # Opcional: solo si usas OpenAI
```

## 🚀 Uso

### Iniciar la aplicación

```bash
streamlit run app.py

# Si la ejecucion anterior falla verifica la version con: python -m streamlit --version
# Si la version es correcta ejecuta:  python -m streamlit run app.py

```

La aplicación se abrirá en tu navegador en `http://localhost:8501`

### Flujo de trabajo

1. **Configurar IA** (Sidebar)

   - Selecciona el modelo de IA
   - Ingresa API Key (si es requerida)

2. **Cargar Datos** (Pestaña 1)

   - Sube archivo Excel con 11 columnas requeridas
   - Valida y visualiza los datos

3. **Generar BPMN** (Pestaña 2)

   - Selecciona tipo de diagrama
   - Genera diagrama BPMN 2.0 interactivo
   - Descarga XML compatible con herramientas BPM

4. **Chat Inteligente** (Pestaña 3)
   - Realiza preguntas sobre optimización
   - Recibe recomendaciones personalizadas

## 📋 Formato de Archivo Excel

### Columnas Requeridas (11 columnas):

1. **Estado Actividad** - Estado actual
2. **Actividades del Proceso** - Nombre de la actividad
3. **Descripción de las Tareas** - Descripción detallada
4. **Cargo que ejecuta la tarea** - Rol responsable
5. **Tarea Automatizada** - SI/NO
6. **No. Colaboradores que ejecutan la tarea** - Número entero
7. **Volumen Promedio Mensual** - Número
8. **Tiempo Menor** - Minutos (numérico)
9. **Tiempo Mayor** - Minutos (numérico)
10. **Tiempo Prom (Min/Tarea)** - Minutos (numérico)
11. **Tiempo Estándar (Min/Tarea)** - Minutos (numérico)

**Nota**: El sistema tiene mapeo inteligente de columnas, por lo que nombres similares serán reconocidos automáticamente.

## 🔑 Configuración de API Keys

### Google Gemini 2.0 (Recomendado para BPMN)

1. Obtén tu API key en: https://makersuite.google.com/app/apikey
2. Ingresa la key en la barra lateral
3. Selecciona "Google Gemini 2.0"

### OpenAI (Opcional)

1. Obtén tu API key en: https://platform.openai.com/api-keys
2. Ingresa la key en la barra lateral
3. Selecciona "OpenAI"

### DeepSeek (Opcional)

1. Obtén tu API key en: https://platform.deepseek.com/
2. Ingresa la key en la barra lateral
3. Selecciona "DeepSeek"

### IA Local (Sin API Key)

- Selecciona "IA Local (Recomendado)"
- No requiere configuración adicional
- Análisis basado en reglas Lean/Six Sigma

## 🎨 Características BPMN

### Tipos de Diagramas

1. **Completo** - Todos los elementos BPMN
2. **Flujo Secuencial** - Proceso lineal
3. **Por Responsables (Pools)** - Agrupado por roles
4. **Enfoque Automatización** - Separación manual/automático

### Elementos BPMN Soportados

- ✅ **Eventos**: Inicio, Fin, Intermedios
- ✅ **Tareas**: User Task, Service Task
- ✅ **Gateways**: Exclusive (XOR)
- ✅ **Pools y Lanes**: Responsables
- ✅ **Subprocesos**: Agrupación de tareas
- ✅ **Boundary Events**: Timers
- ✅ **Message Events**: Throw/Catch

### Compatibilidad

El XML BPMN 2.0 generado es compatible con:

- ✅ Camunda Modeler
- ✅ Bizagi Modeler
- ✅ Signavio
- ✅ Draw.io
- ✅ Cualquier herramienta compatible con BPMN 2.0

## 🔧 Resolución de Problemas

### Error: "No se pudo cargar el archivo"

- Verifica que el archivo sea .xlsx o .xls
- Asegúrate de que tenga las 11 columnas requeridas
- Verifica que no esté corrupto

### Error: "API Key inválida"

- Verifica que la API key sea correcta
- Asegúrate de que tenga permisos activos
- Verifica tu cuota de uso

### El diagrama BPMN no se muestra

- Verifica que tengas conexión a internet (para bpmn-js CDN)
- Actualiza la página (F5)
- Prueba con otro navegador

### Columnas no reconocidas

- El sistema tiene mapeo flexible
- Asegúrate de que los nombres sean similares a los requeridos
- Revisa el mapeo detectado en la vista previa

## 📊 Ejemplos de Uso

### Ejemplo 1: Análisis de proceso de ambulancias

```python
# Los datos deben estar en formato Excel
# El sistema detectará automáticamente:
# - Actividades de espera
# - Transporte innecesario
# - Sobreproceso
# - Oportunidades de automatización
```

### Ejemplo 2: Generación de BPMN para certificación ISO

```python
# Selecciona "Completo" en tipo de diagrama
# El sistema generará:
# - Pools por responsable
# - Lanes por departamento
# - Eventos de inicio/fin estándar
# - Gateways de decisión
```

## 🤝 Contribuciones

Las contribuciones son bienvenidas! Por favor:

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más detalles.

## 👨‍💻 Autor

Desarrollado con ❤️ por el equipo de RAC Assistant

## 🆘 Soporte

¿Necesitas ayuda?

- 📧 Email: support@rac-assistant.com
- 💬 Issues: https://github.com/tu-usuario/rac-assistant/issues
- 📖 Docs: https://rac-assistant.com/docs

## 🗺️ Roadmap

- [ ] Integración con Camunda Cloud
- [ ] Exportar a otros formatos (BPEL, DMN)
- [ ] Simulación de procesos
- [ ] Análisis de costos
- [ ] Optimización con algoritmos genéticos
- [ ] Integración con Power Automate
- [ ] Dashboard de métricas en tiempo real

---
