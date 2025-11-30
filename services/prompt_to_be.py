"""
Módulo para generación de prompts estructurados
"""

import pandas as pd
from typing import Optional, Any

def get_prompt_TOBE(contexto_proceso: str = "", classified_data=None):
    """
    Generar prompt para análisis TO-BE
    
    Args:
        contexto_proceso: Descripción del proceso o contexto del proyecto
        classified_data: DataFrame con datos del Segmentador de Actividades (opcional)
                         Si es None, intentará leerlo de st.session_state.classified_data
        
    Returns:
        Prompt estructurado para análisis TO-BE
    """
    
    # Intentar leer classified_data de session_state si no se proporciona
    if classified_data is None:
        try:
            import streamlit as st
            if hasattr(st, 'session_state') and hasattr(st.session_state, 'get'):
                classified_data = st.session_state.get("classified_data_ca", None)
        except (ImportError, AttributeError):
            # Si streamlit no está disponible, continuar sin classified_data
            pass
    
    contexto_section = ""
    if contexto_proceso and contexto_proceso.strip():
        contexto_section = f"""
### 📋 CONTEXTO DEL PROCESO:
{contexto_proceso}

Este contexto describe el proceso actual (AS-IS) que estás optimizando. Utiliza esta información para:
- Entender mejor el propósito y objetivos del proceso
- Identificar las necesidades específicas del negocio
- Proponer mejoras alineadas con el contexto organizacional
- Asegurar que el proceso TO-BE sea coherente con el entorno del proceso

---
"""
    
    # Sección de datos del Segmentador de Actividades (classified_data)
    segmentador_section = ""
    if classified_data is not None:
        try:
            # Verificar que sea un DataFrame válido
            if isinstance(classified_data, pd.DataFrame) and not classified_data.empty:
                # Obtener información relevante del DataFrame
                total_subactividades = len(classified_data)
                
                # Buscar columnas relevantes (flexible con nombres)
                cols_lower = {col.lower(): col for col in classified_data.columns}
                
                def find_col(*names):
                    for n in names:
                        key = n.lower()
                        if key in cols_lower:
                            return cols_lower[key]
                    return None
                
                col_actividad = find_col('actividad', 'nombre', 'name', 'subactividad')
                col_tipo = find_col('tipo_actividad', 'tipo', 'classification', 'clasificacion')
                col_clasificacion = find_col('clasificacion lean', 'clasificacion_lean', 'clasificacion')
                col_automatizable = find_col('automatizable')
                col_justificacion = find_col('justificacion', 'justificación')
                col_desperdicio = find_col('desperdicio', 'tipo desperdicio', 'waste')
                col_tiempo = find_col('tiempo_promedio_min', 'tiempo_promedio', 'tiempo', 'tiempo_estimado')
                
                # Construir resumen de subactividades
                resumen_subactividades = []
                
                # Agrupar por tipo de actividad si existe
                if col_tipo:
                    tipos_count = classified_data[col_tipo].value_counts().to_dict()
                    tipos_info = ", ".join([f"{k}: {v}" for k, v in tipos_count.items()])
                    resumen_subactividades.append(f"- Tipos de actividad identificados: {tipos_info}")
                
                # Contar automatizables
                if col_automatizable:
                    automatizables = classified_data[col_automatizable].astype(str).str.lower()
                    total_automatizables = (automatizables == "sí").sum() + (automatizables == "si").sum()
                    total_posibles = (automatizables == "posible").sum()
                    if total_automatizables > 0 or total_posibles > 0:
                        resumen_subactividades.append(f"- Actividades automatizables: {total_automatizables}, Posibles: {total_posibles}")
                
                # Contar por clasificación Lean si existe
                if col_clasificacion:
                    clasificaciones = classified_data[col_clasificacion].value_counts().to_dict()
                    clasif_info = ", ".join([f"{k}: {v}" for k, v in clasificaciones.items()])
                    resumen_subactividades.append(f"- Clasificaciones Lean: {clasif_info}")
                
                # Preparar muestra de subactividades (primeras 10 para no hacer el prompt muy largo)
                muestra_subactividades = []
                max_muestra = min(10, total_subactividades)
                
                for idx in range(max_muestra):
                    row = classified_data.iloc[idx]
                    subact_info = {}
                    
                    if col_actividad:
                        subact_info["actividad"] = str(row[col_actividad])[:100]
                    if col_tipo:
                        subact_info["tipo"] = str(row[col_tipo])
                    if col_clasificacion:
                        subact_info["clasificacion"] = str(row[col_clasificacion])
                    if col_automatizable:
                        subact_info["automatizable"] = str(row[col_automatizable])
                    if col_tiempo:
                        tiempo_val = row[col_tiempo]
                        if pd.notna(tiempo_val):
                            subact_info["tiempo_estimado"] = f"{tiempo_val} min"
                    if col_justificacion:
                        just = str(row[col_justificacion])
                        if just and just != "nan":
                            subact_info["justificacion"] = just[:150]
                    
                    if subact_info:
                        muestra_subactividades.append(subact_info)
                
                # Construir la sección del segmentador
                segmentador_section = f"""
### 🔍 DATOS DEL SEGMENTADOR DE ACTIVIDADES:

Se han identificado {total_subactividades} subactividades mediante el Segmentador de Actividades. Esta información es CRÍTICA para tu análisis TO-BE:

*Resumen de Subactividades:*
{chr(10).join(resumen_subactividades) if resumen_subactividades else "- Se identificaron subactividades detalladas del proceso"}

*Muestra de Subactividades Identificadas (primeras {max_muestra} de {total_subactividades}):*
"""
                for i, subact in enumerate(muestra_subactividades, 1):
                    segmentador_section += f"\n{i}. "
                    if "actividad" in subact:
                        segmentador_section += f"{subact['actividad']}"
                    if "tipo" in subact:
                        segmentador_section += f" (Tipo: {subact['tipo']})"
                    if "clasificacion" in subact:
                        segmentador_section += f" [Clasificación: {subact['clasificacion']}]"
                    if "automatizable" in subact:
                        segmentador_section += f" - Automatizable: {subact['automatizable']}"
                    if "tiempo_estimado" in subact:
                        segmentador_section += f" - Tiempo: {subact['tiempo_estimado']}"
                    if "justificacion" in subact:
                        segmentador_section += f"\n   Justificación: {subact['justificacion']}"
                
                segmentador_section += f"""

*INSTRUCCIONES PARA USO DE ESTOS DATOS:*
- Utiliza estas subactividades como base para identificar actividades específicas a optimizar
- Considera las clasificaciones Lean y tipos de actividad al rediseñar el proceso
- Prioriza la automatización de actividades marcadas como automatizables
- Usa los tiempos estimados para calcular mejoras cuantitativas
- Si hay {total_subactividades} subactividades, asegúrate de considerar todas en tu análisis TO-BE

---
"""
        except Exception as e:
            # Si hay error al procesar classified_data, continuar sin esa sección
            # No romper el prompt por errores en el procesamiento
            pass
    
    return f"""
{contexto_section}
{segmentador_section}

Eres un *consultor experto en optimización de procesos, análisis de valor y automatización inteligente*, 
especializado en metodologías *Lean Six Sigma, BPMN, Kaizen, SCAMPER y RPA (Robotic Process Automation)*.

Utiliza los resultados que arroja el proceso de segmentación de actividades que han sido procesados previamente.

Tu ÚNICO objetivo es:
-Analizar el proceso actual (AS-IS) y generar una tabla con todas las actividades del proceso, identificando cuáles de esas actividades se pueden optimizar en un nuevo proceso.

 *INSTRUCCIONES:*

1. Lista TODAS las actividades del proceso que se está analizando en una tabla.
   - Si se proporcionaron subactividades segmentadas, usa esa información como base
   - Si no hay subactividades, analiza el proceso desde el contexto proporcionado
2. Para cada actividad, indica si se puede optimizar en un nuevo proceso.
   - Considera los tiempos estimados, dependencias y tipo de actividad
   - Evalúa si la actividad es automatizable según la información proporcionada
3. Si una actividad se puede optimizar, menciona brevemente cómo se podría optimizar.


*ESTIMACIÓN DE TIEMPO MEJORADO (CRÍTICO):*

Para cada actividad rediseñada, DEBES estimar el tiempo mejorado basándote en:

1. *Tiempo Original (AS-IS)*: Usa el tiempo promedio en minutos por tarea que se proporciona en los datos.
2. *Número de Personas*: Considera cuántas personas realizan la tarea originalmente.
3. *Tipo de Optimización*:
   - *Eliminada*: Tiempo = 0 minutos, personas = 0
   - *Automatizada*: Reduce tiempo en 60-90% (dependiendo del nivel de automatización)
   - *Optimizada*: Reduce tiempo en 20-50% (según la optimización aplicada)
   - *Combinada*: Suma los tiempos de las actividades combinadas y reduce en 10-30% por eficiencia
   - *Conservada*: Mantiene tiempo similar o mejora marginal (0-10%)

4. *Cálculo de Personas*:
   - Si se automatiza: Reduce personas según el nivel de automatización
   - Si se combina: Suma personas y ajusta según eficiencia
   - Si se optimiza: Puede mantener o reducir personas según el caso

5. *Tiempo Total del Proceso*: Calcula el tiempo total del proceso TO-BE sumando todas las actividades optimizadas.

IMPORTANTE: 
- Realiza rediseño de actividades y propon una mejora en el proceso futuro (TO-BE) usando optimización Lean Six Sigma.
- SIEMPRE incluye estimaciones de tiempo mejorado para cada actividad rediseñada.
- Las estimaciones deben ser realistas y justificadas según el tipo de optimización aplicada.

*RESPONDE ÚNICAMENTE EN FORMATO JSON* con esta estructura exacta:

{{
  "actividades_optimizadas": [
    {{
      "actividad": "<nombre de la actividad>",
      "descripcion": "<descripción>",
      "clasificacion_original": "VA|NVA-N|NVA-P",
      "accion": "Eliminada|Optimizada|Automatizada|Conservada|Combinada",
      "justificacion": "<razón de la acción>",
      "recomendacion_aplicada": "<recomendación del clasificador aplicada>",
      "tipo_desperdicio_eliminado": "<código si aplica>",
      "tiempo_original_minutos": <número - tiempo promedio original en minutos por tarea>,
      "personas_originales": <número - número de personas que ejecutan la tarea originalmente>,
      "tiempo_mejorado_minutos": <número - tiempo estimado mejorado en minutos por tarea>,
      "personas_mejoradas": <número - número de personas estimadas después de la optimización>,
      "reduccion_tiempo_porcentaje": <número - porcentaje de reducción de tiempo (0-100)>,
      "justificacion_tiempo": "<explicación breve de cómo se estimó el tiempo mejorado>"
    }}
  ],
  "sipoc": {{
    "suppliers": ["<proveedor1>", "<proveedor2>", ...],
    "inputs": ["<entrada1>", "<entrada2>", ...],
    "process": [
      {{
        "paso": 1,
        "nombre": "<nombre del paso>",
        "descripcion": "<descripción del paso>"
      }}
    ],
    "outputs": ["<salida1>", "<salida2>", ...],
    "customers": ["<cliente1>", "<cliente2>", ...]
  }},
  "mejoras_cuantitativas": {{
    "actividades_eliminadas": <número>,
    "actividades_optimizadas": <número>,
    "tiempo_total_original_minutos": <número - suma de todos los tiempos originales>,
    "tiempo_total_mejorado_minutos": <número - suma de todos los tiempos mejorados>,
    "reduccion_tiempo_total_porcentaje": <número - porcentaje de reducción del tiempo total del proceso>,
    "personas_totales_originales": <número - suma de todas las personas originales>,
    "personas_totales_mejoradas": <número - suma de todas las personas mejoradas>,
    "reduccion_personas_porcentaje": <número - porcentaje de reducción de personal>,
    "reduccion_costo_estimada": "<porcentaje o descripción basada en reducción de tiempo y personal>",
    "mejora_calidad": "<descripción>"
  }}
}}

*REGLAS IMPORTANTES:*
- NO incluyas ningún texto adicional, solo el JSON válido
- NO uses bloques de código markdown (```json)
- Asegúrate de que el JSON sea válido y parseable
- La tabla debe incluir TODAS las actividades del proceso analizado
- Sé claro y conciso en las descripciones de optimización

Responde AHORA con el JSON:"""
