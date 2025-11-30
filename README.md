# 🚀 RAC Assistant -- Optimización Inteligente de Procesos

**Proyecto Maestría en Inteligencia Artificial Aplicada**\
**Universidad Icesi -- Cali, Colombia**

------------------------------------------------------------------------

## 🔹 Estado del Proyecto

**Status:** ✅ Activo

------------------------------------------------------------------------

## 👥 Integrantes del Proyecto

| Rol | Nombre | GitHub |
|-----|--------|--------|
| Integrante | Jean Pierre Londoño | https://github.com/jepilogo97 |
| Integrante | Julio Morales | https://github.com/ |
| Integrante | Jonathan Pacheco | https://github.com/ |
| Integrante | Joshua Triana | https://github.com/ |
| Integrante | Javier Yela | https://github.com/ |
| **Instructor** | **Jose Armando Ordoñez** | https://github.com/ |

------------------------------------------------------------------------

## 📫 Contacto

📧 Email: support@rac-assistant.com\
💬 GitHub Issues: https://github.com/jepilogo97/rac-assistant/issues

------------------------------------------------------------------------

## 🎯 Objetivo del Proyecto

El propósito de este proyecto es diseñar e implementar un sistema
inteligente para el análisis, documentación y optimización de procesos
empresariales mediante Inteligencia Artificial. El sistema transforma
datos estructurados en diagramas BPMN 2.0, identifica ineficiencias
utilizando Lean y Six Sigma, y genera propuestas de optimización TO-BE.
Este proyecto contribuye a la transformación digital organizacional
facilitando la mejora continua basada en datos.

------------------------------------------------------------------------

## 🧪 Métodos Utilizados

-   Análisis de Procesos Empresariales (AS-IS / TO-BE)
-   Lean Manufacturing
-   Six Sigma -- Clasificación VAC / VAN / SVA
-   Inteligencia Artificial Generativa (Gemini 2.0)
-   Validación de Datos y Segmentación de Procesos
-   Análisis de KPIs y Métricas de Desempeño

------------------------------------------------------------------------

## 🛠️ Tecnologías

-   Python 3.10+
-   Streamlit
-   Pandas, OpenPyXL
-   Google Gemini 2.0
-   bpmn-js, Plotly
-   Git & GitHub

------------------------------------------------------------------------

## 📖 Descripción del Proyecto

RAC Assistant es una aplicación web inteligente orientada a la
automatización del análisis y la optimización de procesos empresariales.
Recibe datos del proceso en formato Excel y ejecuta validación,
generación de diagramas BPMN, análisis Lean, clasificación Six Sigma,
segmentación de procesos y generación automática de propuestas TO-BE con
indicadores de desempeño.

------------------------------------------------------------------------

## 🏗️ Arquitectura del Proyecto

    proyecto_final_mia/
    ├── app.py                      # Punto de entrada principal
    ├── run.py                      # Script alternativo de ejecución
    ├── config.py                   # Configuración general
    ├── requirements.txt            # Dependencias del proyecto
    │
    ├── services/                   # Lógica de negocio
    │   ├── analysis.py             # Análisis de desperdicios Lean
    │   ├── bpmn.py                 # Generación BPMN 2.0
    │   ├── classification.py       # Clasificación Six Sigma
    │   ├── data_processing.py      # Procesamiento de archivos Excel
    │   ├── dependency_validator.py # Validación de dependencias
    │   ├── file_utils.py           # Utilidades de archivos
    │   ├── gemini_utils.py         # Integración con Gemini
    │   ├── prompt_to_be.py         # Generación TO-BE
    │   └── segmentation.py         # Segmentación de procesos
    │
    ├── ui/                         # Interfaz de usuario
    │   ├── common.py               # Componentes comunes de interfaz
    │   ├── layout.py               # Estructura principal de la app
    │   ├── styles.py               # Estilos personalizados
    │   ├── validator_controller.py # Controlador de validación
    │   └── tabs/
    │       ├── upload.py           # Carga de archivos
    │       ├── process.py          # Análisis AS-IS
    │       ├── classifier.py       # Clasificador Six Sigma
    │       ├── segmenter.py        # Segmentador de procesos
    │       ├── tobe.py             # Generación TO-BE
    │       └── kpis.py             # Dashboard de KPIs
    │
    └── files-example/              # Archivos de ejemplo

------------------------------------------------------------------------

## 📦 Instalación

``` bash
git clone https://github.com/tu-usuario/rac-assistant.git
cd rac-assistant
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

------------------------------------------------------------------------

## 🚀 Ejecución

``` bash
streamlit run app.py
```

------------------------------------------------------------------------

## 📄 Fuente de Datos

Datos ingresados por el usuario mediante archivos Excel (.xlsx).
Ejemplos disponibles en la carpeta /files-example.

------------------------------------------------------------------------

## 📊 Formato del Archivo Excel

1.  Estado Actividad\
2.  Actividades del Proceso\
3.  Descripción de las Tareas\
4.  Cargo que ejecuta\
5.  Tarea Automatizada\
6.  Número de Colaboradores\
7.  Volumen Promedio Mensual\
8.  Tiempo Menor\
9.  Tiempo Mayor\
10. Tiempo Promedio\
11. Tiempo Estándar

------------------------------------------------------------------------

## 🔑 Configuración de la API

Se requiere una API Key de Google Gemini 2.0 para las funciones de IA.

------------------------------------------------------------------------

## 🧪 Casos de Uso

-   Documentación de procesos empresariales
-   Optimización de procesos operativos
-   Análisis para certificaciones ISO
-   Modelado académico de procesos

------------------------------------------------------------------------

## 📊 Roadmap

### Versión 2.0

-   Simulación de procesos
-   Análisis de costos
-   Exportación multi-formato

### Versión 3.0

-   Predicción de optimización con ML
-   Integración con Power Automate
-   Dashboard ejecutivo

------------------------------------------------------------------------

## 📝 Licencia

MIT License

------------------------------------------------------------------------

## 📌 Citación

Londoño, J. - Morales, J. - Pacheco, J. - Triana, J.- Yela, J. (2025). Agente Inteligente Automatizado para la Mejora Continua de Procesos. Universidad Icesi.



