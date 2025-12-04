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
        # En entorno backend, classified_data debe ser proporcionado explícitamente
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

    # Sección de Documentación Complementaria (RAG)
    rag_section = ""
    try:
        from services.rag import get_rag_context
        rag_content = get_rag_context()
        if rag_content:
            rag_section = f"""
###📚 DOCUMENTACIÓN COMPLEMENTARIA (RAG):
La siguiente información proviene de documentos y guías cargados en el sistema (PDFs, Excel). 
Úsala como referencia obligatoria para alinear las propuestas con los estándares y conocimientos de la organización:

{rag_content}

---
"""
    except Exception as e:
        print(f"⚠️ Warning: Could not load RAG context: {e}")
        rag_section = ""

    
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
                    try:
                        for n in names:
                            key = n.lower()
                            if key in cols_lower:
                                return cols_lower[key]
                    except:
                        pass
                    return None
                
                # Try to build summary, but fallback if any error occurs
                try:
                    print(f"DEBUG: DataFrame columns: {classified_data.columns.tolist()}")
                    if not classified_data.empty:
                        print(f"DEBUG: First row sample: {classified_data.iloc[0].to_dict()}")

                    col_actividad = find_col('actividad', 'nombre', 'name', 'subactividad', 'step', 'paso')
                    col_tipo = find_col('tipo_actividad', 'tipo', 'classification', 'clasificacion')
                    col_clasificacion = find_col('clasificacion lean', 'clasificacion_lean', 'clasificacion', 'lean')
                    col_automatizable = find_col('automatizable', 'automation')
                    col_justificacion = find_col('justificacion', 'justificación', 'reason')
                    col_desperdicio = find_col('desperdicio', 'tipo desperdicio', 'waste', 'tipo_desperdicio')
                    col_tiempo = find_col('tiempo estándar', 'Tiempo Estándar', 'tiempo_estandar', 'tiempo_promedio_min', 'tiempo_promedio', 'tiempo', 'tiempo_estimado', 'time', 'duration')
                    
                    # Fallback for time column if not found
                    if not col_tiempo:
                        for col in classified_data.columns:
                            if 'tiempo' in col.lower() or 'time' in col.lower():
                                col_tiempo = col
                                break
                    
                    print(f"DEBUG: Found columns - Time: {col_tiempo}, Activity: {col_actividad}")
                    
                    # Construir resumen de subactividades
                    resumen_subactividades = []
                    
                    # Contar automatizables
                    if col_automatizable and col_automatizable in classified_data.columns:
                        try:
                            automatizables = classified_data[col_automatizable].astype(str).str.lower()
                            total_automatizables = (automatizables == "sí").sum() + (automatizables == "si").sum()
                            total_posibles = (automatizables == "posible").sum()
                            if total_automatizables > 0 or total_posibles > 0:
                                resumen_subactividades.append(f"- Actividades automatizables: {total_automatizables}, Posibles: {total_posibles}")
                        except:
                            pass
                    
                    # Contar por clasificación Lean
                    if col_clasificacion and col_clasificacion in classified_data.columns:
                        try:
                            clasificaciones = classified_data[col_clasificacion].value_counts().to_dict()
                            clasif_info = ", ".join([f"{k}: {v}" for k,v in clasificaciones.items()])
                            resumen_subactividades.append(f"- Clasificaciones Lean: {clasif_info}")
                        except:
                            pass
                except Exception as e:
                    print(f"Warning: Could not build detailed summary: {e}")
                    resumen_subactividades = [f"Total actividades: {total_subactividades}"]
                
                # Build detailed list of all activities
                newline = "\n"
                resumen_text = newline.join(resumen_subactividades) if resumen_subactividades else ""
                
                activities_list = []
                if not classified_data.empty:
                    for idx, row in classified_data.iterrows():
                        act_id = row.get('id', idx + 1)
                        nombre = row.get(col_actividad, 'Sin nombre') if col_actividad else row.get('nombre', 'Sin nombre')
                        tiempo = row.get(col_tiempo, 0) if col_tiempo else 0
                        tipo = row.get(col_tipo, 'N/A') if col_tipo else 'N/A'
                        auto = row.get(col_automatizable, 'N/A') if col_automatizable else 'N/A'
                        
                        activities_list.append(f"- ID: {act_id} | Actividad: {nombre} | Tiempo Original: {tiempo} min | Tipo: {tipo} | Automatizable: {auto}")
                
                activities_text = "\n".join(activities_list)
                
                segmentador_section = f"""
### 🔍 DATOS DEL SEGMENTADOR DE ACTIVIDADES:

Total de actividades analizadas: **{total_subactividades}**

{resumen_text}

**LISTADO COMPLETO DE ACTIVIDADES (Usa estos datos EXACTOS para 'tiempo_original_minutos'):**

{activities_text}

---
"""
        except Exception as e:
            print(f"⚠️ Error processing classified_data in prompt: {e}")
            # Fallback: just include raw info
            segmentador_section = f"""
### 🔍 DATOS DEL SEGMENTADOR:
Se proporcionaron {len(classified_data) if hasattr(classified_data, '__len__') else 'varios'} registros de actividades.
Úsalos como base para el análisis TO-BE.

---
"""
    
    return f"""
{contexto_section}
{rag_section}
{segmentador_section}

Eres un **consultor experto en optimización de procesos, análisis de valor y automatización inteligente**, 
especializado en metodologías **Lean Six Sigma, BPMN, Kaizen, SCAMPER y RPA (Robotic Process Automation)**.

Tu ÚNICO objetivo es:
- Analizar el proceso actual (AS-IS) y generar una propuesta de proceso optimizado (TO-BE) con mejoras concretas.

**INSTRUCCIONES:**

1. Analiza TODAS las actividades del proceso AS-IS
2. Para cada actividad, determina si se debe:
   - **Eliminar** (no agrega valor)
   - **Automatizar** (puede ser automatizada total o parcialmente)
   - **Optimizar** (mejorar sin eliminar ni automatizar)
   - **Mantener** (ya es eficiente)
   - **Combinar** (fusionar con otras actividades)

3. Para cada actividad rediseñada, calcula:
   - Tiempo mejorado en minutos
   - Número de personas necesarias
   - Porcentaje de reducción de tiempo

**ESTIMACIÓN DE TIEMPO MEJORADO (CRÍTICO):**

Para cada actividad rediseñada, DEBES estimar el tiempo mejorado basándote en:

1. **Tiempo Original (AS-IS)**: 
   - ⚠️ **IMPORTANTE**: Debes COPIAR EXACTAMENTE el valor de 'Tiempo Original' de la lista de actividades proporcionada arriba.
   - ⚠️ **NO INVENTES** tiempos originales. Si dice 5.5, pon 5.5. Si dice 0, pon 0.
   - Este valor es la base para calcular la reducción.
2. **Tipo de Optimización**:
   - **Eliminada**: Tiempo = 0 minutos, personas = 0
   - **Automatizada**: Reduce tiempo en 70-90% (dependiendo del nivel)
   - **Optimizada**: Reduce tiempo en 20-50%
   - **Combinada**: Suma tiempos y reduce en 20-40% por eficiencia
   - **Mantenida**: Mismo tiempo

3. **Personas**: Estima cuántas personas se necesitan (original vs mejorado)

**FORMATO DE RESPUESTA:**

Devuelve un JSON con esta estructura EXACTA:

{{
  "actividades_optimizadas": [
    {{
      "id": 1,
      "nombre": "<nombre de la actividad>",
      "descripcion": "<descripción detallada del paso optimizado>",
      "accion": "Eliminada|Automatizada|Optimizada|Mantenida|Combinada",
      "justificacion": "<por qué se aplicó esta acción específica>",
      "tiempo_original_minutos": <número>,
      "personas_originales": <número>,
      "tiempo_mejorado_minutos": <número>,
      "personas_mejoradas": <número>,
      "reduccion_tiempo_porcentaje": <número>
    }}
  ],
  "sipoc": {{
    "suppliers": ["<proveedor1>", "<proveedor2>"],
    "inputs": ["<entrada1>", "<entrada2>"],
    "process": [
      {{
        "paso": 1,
        "nombre": "<nombre del paso>",
        "descripcion": "<descripción del paso>"
      }}
    ],
    "outputs": ["<salida1>", "<salida2>"],
    "customers": ["<cliente1>", "<cliente2>"]
  }},
  "mejoras_cuantitativas": {{
    "actividades_eliminadas": <número>,
    "actividades_automatizadas": <número>,
    "actividades_optimizadas": <número>,
    "actividades_combinadas": <número>,
    "tiempo_total_original_minutos": <suma de todos los tiempos originales>,
    "tiempo_total_mejorado_minutos": <suma de todos los tiempos mejorados>,
    "reduccion_tiempo_total_porcentaje": <porcentaje de reducción>,
    "personas_totales_originales": <suma de personas originales>,
    "personas_totales_mejoradas": <suma de personas mejoradas>,
    "reduccion_personas_porcentaje": <porcentaje de reducción de personal>,
    "reduccion_costo_estimada": "<descripción del ahorro estimado>",
    "mejora_calidad": "<descripción de mejoras en calidad>"
  }}
}}

**REGLAS IMPORTANTES:**
- NO incluyas texto adicional, SOLO el JSON
- NO uses bloques de código markdown (```json)
- El JSON debe ser válido y parseable
- Incluye TODAS las actividades del proceso
- Sé realista en las estimaciones de tiempo
- Justifica cada decisión de optimización

Responde AHORA con el JSON:"""
