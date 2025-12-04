"""
Servicio de Segmentación de Procesos (As-Is) con Gemini 2.0
Divide un proceso en subactividades clasificadas por tipo funcional.
Clasifica: Operativa | Analítica | Cognitiva.
Basado en metodologías Lean, Six Sigma, Kaizen y SCAMPER
"""

import pandas as pd
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import google.generativeai as genai
import time
import re
import hashlib
import os
from services.gemini_utils import initialize_gemini


# Simple in-memory cache for classifications
_classification_cache: Dict[str, Dict[str, str]] = {}
_segment_page_cache: Dict[str, List[Dict[str, Any]]] = {}

def _extract_json_from_text(text: str) -> Optional[str]:
  """Intentar extraer un bloque JSON válido desde un texto libre."""
  if not text or not isinstance(text, str):
    return None

  start = text.find('{')
  if start == -1:
    return None

  depth = 0
  end = None
  for i in range(start, len(text)):
    ch = text[i]
    if ch == '{':
      depth += 1
    elif ch == '}':
      depth -= 1
      if depth == 0:
                end = i
                break

    if end is None:
        return None

    candidate = text[start:end+1]
    candidate = candidate.strip()
    return candidate


def _extract_json_array_from_text(text: str) -> Optional[str]:
    """Extrae el primer array JSON balanceado ([...]) desde un texto libre."""
    if not text or not isinstance(text, str):
        return None

    start = text.find('[')
    if start == -1:
        return None

    depth = 0
    end = None
    for i in range(start, len(text)):
        ch = text[i]
        if ch == '[':
            depth += 1
        elif ch == ']':
            depth -= 1
            if depth == 0:
                end = i
                break

    if end is None:
        return None

    candidate = text[start:end+1].strip()
    return candidate

def _attempt_json_fixes(text: str) -> Optional[Dict[str, Any]]:
    """Aplicar correcciones comunes para intentar parsear JSON defectuoso."""
    if not isinstance(text, str) or not text.strip():
        return None

    cleaned = (
        text.replace("```json", "").replace("```", "")
            .replace('“', '"').replace('”', '"')
            .replace("’", "'").replace('—', '-')
            .strip()
    )

    cleaned = re.sub(r",\s*\]", "]", cleaned)
    cleaned = re.sub(r",\s*\}", "}", cleaned)

    try:
        return json.loads(cleaned)
    except Exception:
        pass

    cand = _extract_json_from_text(cleaned)
    if cand:
        try:
            return json.loads(cand)
        except Exception:
            cand2 = re.sub(r",\s*\]", "]", cand)
            cand2 = re.sub(r",\s*\}", "}", cand2)
            try:
                return json.loads(cand2)
            except Exception:
                pass

    arr_cand = _extract_json_array_from_text(cleaned)
    if arr_cand:
        try:
            arr = json.loads(arr_cand)
            return {"subactividades": arr}
        except Exception:
            pass

    return None


def create_subactivities_prompt(proceso_general: str, proceso_as_is: str) -> str:
        """Prompt de segmentación Lean Six Sigma."""
        if not proceso_as_is or proceso_as_is.isspace():
                raise ValueError("La descripción del proceso As-Is no puede estar vacía")
        return f"""Eres un analista Lean Six Sigma. Clasifica y enriquece las actividades del proceso.

Proceso: {proceso_general}
AsIs:
<<INICIO>>
{proceso_as_is}
<<FIN>>

🚫 REGLAS DE SUBDIVISIÓN (CRÍTICAS - CUMPLIMIENTO OBLIGATORIO):

1. **REGLA PRINCIPAL**: Por DEFECTO, NO dividas actividades. Mantén 1:1
2. **EXCEPCIÓN ÚNICA**: Solo divide si la actividad es EXTREMADAMENTE compleja y contiene claramente 2 tareas distintas
3. **LÍMITE ABSOLUTO**: NUNCA dividas en más de 2 subactividades
4. **OBJETIVO**: Mínimo 80% de actividades deben mantenerse 1:1 (sin dividir)

📊 CONTEO ESPERADO (VERIFICACIÓN OBLIGATORIA):
- Cuenta actividades en As-Is = N
- Tu respuesta DEBE tener: Entre N y N+3 actividades (MÁXIMO)
- Ejemplo: As-Is con 14 actividades → Respuesta: 14-17 actividades ✅
- Si As-Is tiene 14 actividades y respondes con 50 → ❌ INCORRECTO

⏱️ REGLA DE TIEMPOS (CRÍTICA - VERIFICACIÓN MATEMÁTICA OBLIGATORIA):

**ANTES de generar el JSON, DEBES:**
1. Sumar TODOS los tiempos que vas a asignar
2. Verificar que la suma EXACTA = suma de tiempos originales
3. Si divides una actividad de 60 min en 2:
   - Opción A: 30 + 30 = 60 ✅
   - Opción B: 40 + 20 = 60 ✅
   - NUNCA: 40 + 40 = 80 ❌ (esto DUPLICA el tiempo)

**FÓRMULA DE VERIFICACIÓN:**
```
Suma(tiempos_originales) = Suma(tiempos_nuevos)
```

**DISTRIBUCIÓN DE TIEMPOS AL DIVIDIR:**
- Si divides una actividad, distribuye el tiempo proporcionalmente
- Ejemplo: Actividad de 100 min dividida en 2 tareas:
  * Si tarea 1 es 70% del trabajo → 70 min
  * Si tarea 2 es 30% del trabajo → 30 min
  * Total: 70 + 30 = 100 ✅

CLASIFICACIÓN LEAN (OBLIGATORIA):
- VA: Transforma producto/servicio, cliente pagaría
- NVA-N: No agrega valor pero necesario (regulación)
- NVA: Desperdicio (Sobreproducción, Espera, Transporte, Sobreprocesamiento, Inventario, Movimiento, Defectos, Talento)

TIPO DE ACTIVIDAD:
- Operativa: Hacer, ejecutar, mover
- Analítica: Medir, calcular, datos
- Cognitiva: Decidir, revisar, aprobar

CAMPOS OBLIGATORIOS:
- id: número secuencial
- nombre: descriptivo
- descripcion, objetivo
- responsable: cargo del As-Is
- tipo_actividad: Operativa|Analítica|Cognitiva
- clasificacion_lean: VA|NVA-N|NVA
- tipo_desperdicio: si NVA, especificar tipo
- justificacion: por qué esa clasificación
- dependencias: null o id previo
- tiempo_promedio_min, tiempo_estimado_total_min
- automatizable: Si|No|Posible
- sugerencia_automatizacion: si != No
- actividad_original_id: número de actividad original (1 a N)

JSON:
{{
    "proceso": "{proceso_general}",
    "numero_subactividades": <entre N y N+5>,
    "subactividades": [
        {{
            "id": 1,
            "nombre": "nombre actividad",
            "descripcion": "...",
            "objetivo": "...",
            "responsable": "cargo",
            "tipo_actividad": "Operativa|Analítica|Cognitiva",
            "clasificacion_lean": "VA|NVA-N|NVA",
            "tipo_desperdicio": "tipo o null",
            "justificacion": "razón",
            "dependencias": null,
            "tiempo_promedio_min": 10,
            "tiempo_estimado_total_min": 10,
            "automatizable": "Si|No|Posible",
            "sugerencia_automatizacion": "cómo o null",
            "actividad_original_id": 1
        }}
    ]
}}

VERIFICACIÓN FINAL OBLIGATORIA:
1. Contar actividades As-Is = N
2. Contar actividades en tu respuesta = M
3. Verificar: N ≤ M ≤ N+3 ✅
4. Sumar tiempo_promedio_min de todas las subactividades
5. Verificar que suma = tiempo total original ✅
6. Si alguna verificación falla → CORREGIR antes de responder
"""











def create_subactivities_prompt_page(proceso_general: str, proceso_as_is: str, start: int = 0, page_size: int = 5) -> str:
    """Prompt paginado alineado con el esquema estricto."""
    base = create_subactivities_prompt(proceso_general, proceso_as_is)
    rango_inicio = start + 1
    rango_fin = start + page_size
    instrucciones_paginacion = (
        "\n\nREGLAS DE PAGINACIÓN (ESTE BLOQUE ES MANDATORIO):\n"
        f"- Devuelve SOLO subactividades con id entre {rango_inicio} y {rango_fin} (inclusive).\n"
        "- Mantén el conteo y los ids coherentes con el esquema; no repitas ni saltes ids fuera del rango.\n"
        "- Continúa los IDs globalmente desde el último valor; NO reinicies IDs por página.\n"
        f"- Ids solicitados (rango actual): {rango_inicio}-{rango_fin}.\n"
        "- Si no hay subactividades en ese rango, devuelve un array vacío: [] (sin texto adicional).\n"
        "- Preferencia de respuesta: objeto completo con clave \"subactividades\" filtrada por el rango.\n"
        "  Alternativamente (para reducir tokens), puedes responder SOLO con el array JSON de \"subactividades\".\n"
        "- No retornes markdown, encabezados, ni comentarios. Solo JSON válido.\n"
        "\n"
        "FORMATO DE RESPUESTA (CRÍTICO - MANDATORIO):\n"
        "1. SOLO devuelve JSON válido y completo, sin texto adicional antes o después\n"
        "2. NO uses delimitadores markdown (NO ```json ni ```)\n"
        "3. NO agregues comentarios, explicaciones, notas ni texto narrativo\n"
        "4. Asegúrate de cerrar TODAS las llaves {} y corchetes [] correctamente\n"
        "5. Si el JSON es muy grande y alcanzas el límite de tokens:\n"
        "   - Prioriza completar el array \"subactividades\" con objetos completos\n"
        "   - Es mejor devolver menos subactividades completas que muchas incompletas\n"
        "6. Verifica que cada objeto en \"subactividades\" tenga TODOS los campos requeridos\n"
        "7. Si no hay suficiente información, usa valores por defecto razonables pero NO omitas campos\n"
    )
    return base + instrucciones_paginacion


def _normalize_subactivities(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normaliza subactividades."""
    allowed = {"id","nombre","descripcion","objetivo","tipo_actividad","dependencias","tiempo_promedio_min","tiempo_estimado_total_min","automatizable","sugerencia_automatizacion", "actividad_original_id"}
    cleaned: List[Dict[str, Any]] = []
    next_id = 1
    for r in (records or []):
        if not isinstance(r, dict):
            continue
        rid = r.get("id")
        if not isinstance(rid, int) or rid is None or rid < 1:
            rid = next_id
        next_id = rid + 1
        c: Dict[str, Any] = {"id": rid}
        for k in allowed - {"id"}:
            v = r.get(k)
            if k in ("tiempo_promedio_min","tiempo_estimado_total_min"):
                try:
                    v = int(v)
                    if v < 1:
                        v = 1
                except Exception:
                    v = 1
            if k == "dependencias" and v not in (None, "", [], "null"):
                try:
                    v = int(v)
                    if v == rid or v < 1:
                        v = rid - 1 if rid > 1 else None
                except Exception:
                    v = None
            if isinstance(v, str) and len(v) > 1000:
                v = v[:1000] + "…"
            c[k] = v
        cleaned.append(c)
    return cleaned


def export_segmentation_report(df_segmented: pd.DataFrame) -> bytes:
    """
    Exportar reporte de segmentación a Excel
    """
    from io import BytesIO
    output = BytesIO()
    
    # Ensure all columns exist
    columns_order = [
        'id', 'Actividad', 'Descripción', 'Cargo que ejecuta la tarea', 
        'Clasificación Lean', 'Tipo Desperdicio', 'Justificación', 
        'Tiempo Estándar', 'tipo_actividad', 'automatizable', 'sugerencia_automatizacion'
    ]
    
    # Map internal names to display names if needed or ensure columns exist
    # This is a basic mapping, might need adjustment based on exact DF structure
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_segmented.to_excel(writer, sheet_name='Segmentación', index=False)
        
        # Adjust column widths
        worksheet = writer.sheets['Segmentación']
        for idx, col in enumerate(df_segmented.columns):
            max_len = max(
                df_segmented[col].astype(str).map(len).max(),
                len(str(col))
            ) + 2
            # Cap max width
            if max_len > 50:
                max_len = 50
            worksheet.column_dimensions[chr(65 + idx)].width = max_len
            
    return output.getvalue()


def _coerce_subactivities_min_schema(result: Dict[str, Any]) -> Dict[str, Any]:
    """Intenta salvar respuestas parciales llenando campos faltantes con valores por defecto."""
    if not isinstance(result, dict):
        return result
    
    subacts = result.get("subactividades", [])
    if not isinstance(subacts, list):
        return result
    
    defaults = {
        "id": 0,
        "nombre": "Sin nombre",
        "descripcion": "Sin descripción",
        "objetivo": "Sin objetivo",
        "tipo_actividad": "Operativa",
        "dependencias": None,
        "tiempo_promedio_min": 5,
        "tiempo_estimado_total_min": 5,
        "automatizable": "No",
        "sugerencia_automatizacion": None
    }
    
    coerced = []
    for i, item in enumerate(subacts):
        if not isinstance(item, dict):
            continue
        for key, default_val in defaults.items():
            if key not in item:
                item[key] = default_val
        if item["id"] == 0:
            item["id"] = i + 1
        coerced.append(item)
    
    result["subactividades"] = coerced
    return result


def _validate_subactivities_schema(result: Dict[str, Any]) -> bool:
    """Validación estricta del esquema retornado por Gemini."""
    if not isinstance(result, dict):
        return False
    if "subactividades" not in result:
        return False
    subacts = result.get("subactividades")
    if not isinstance(subacts, list):
        return False
    for item in subacts:
        if not isinstance(item, dict):
            return False
        required = [
            "id",
            "nombre",
            "descripcion",
            "objetivo",
            "tipo_actividad",
            "dependencias",
            "tiempo_promedio_min",
            "tiempo_estimado_total_min",
            "automatizable",
        ]
        if any(k not in item for k in required):
            return False
    return True

def _fix_dependencies_consistency(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Asegura que dependencias nunca apunten a IDs inexistentes ni circulares."""
    valid_ids = {r.get("id") for r in records if isinstance(r, dict)}
    for r in records:
        try:
            dep = r.get("dependencias")
            rid = r.get("id")
            if dep not in valid_ids or dep == rid:
                r["dependencias"] = None
        except Exception:
            r["dependencias"] = None
    return records

def segment_process(proceso_general: str, proceso_as_is: str, api_key: str, batch_mode: bool = True, progress_callback=None, max_pages: int = 20, page_size: int = 7, use_cache: bool = True, force_reclassify: bool = False) -> pd.DataFrame:
    """
    Generar subactividades del proceso usando Gemini
    """
    if not initialize_gemini(api_key):
        print("No se pudo inicializar Gemini")
        return pd.DataFrame()

    prompt = create_subactivities_prompt(proceso_general, proceso_as_is)
    max_retries = 3
    base_delay = 1
    
    models_to_try = ["gemini-2.0-flash", "gemini-1.5-flash"]
    current_model_index = 0
    
    model = genai.GenerativeModel(
        model_name=models_to_try[current_model_index],
        generation_config={
            "temperature": 0.10,
            "max_output_tokens": 2048,
        },
    )

    start = 0
    all_subacts: List[Dict[str, Any]] = []

    end_of_data = False
    for page in range(max_pages):
        # Create a hash of the content to ensure cache uniqueness
        try:
            content_hash = hashlib.md5(str(proceso_as_is).encode('utf-8', errors='ignore')).hexdigest()
        except Exception:
            content_hash = "no_hash"
            
        cache_key = f"{proceso_general[:40]}|{content_hash}|{start}|{page_size}"
        if use_cache and cache_key in _segment_page_cache:
            subacts_page = _segment_page_cache[cache_key]
            all_subacts.extend(subacts_page)
            if len(subacts_page) < page_size:
                end_of_data = True
                break
            start += page_size
            continue

        prompt_page = create_subactivities_prompt_page(proceso_general, proceso_as_is, start=start, page_size=page_size)

        for attempt in range(1, max_retries + 1):
            try:
                response = model.generate_content(prompt_page)
                resp_text = getattr(response, "text", None)
                if resp_text is None:
                    try:
                        resp_text = json.dumps(response.to_dict())
                    except Exception:
                        resp_text = str(response)

                clean_text = str(resp_text).strip().replace("```json", "").replace("```", "").strip()
                result = None
                candidate = _extract_json_from_text(clean_text)
                if candidate:
                    try:
                        result = json.loads(candidate)
                    except Exception:
                        result = None

                if result is None:
                    result = _attempt_json_fixes(clean_text)
                    if result is None:
                        result = _attempt_json_fixes(resp_text)

                if result is None:
                    m = re.search(r"\{.*\}", resp_text, re.DOTALL)
                    if m:
                        cand = m.group(0)
                        result = _attempt_json_fixes(cand)

                if result is None:
                    arr_candidate = None
                    try:
                        arr_candidate = _extract_json_array_from_text(clean_text) or _extract_json_array_from_text(resp_text)
                    except Exception:
                        arr_candidate = None

                    if arr_candidate:
                        try:
                            arr = json.loads(arr_candidate)
                            result = {"subactividades": arr, "proceso": proceso_general}
                        except Exception:
                            result = None

                if result is not None:
                    result = _coerce_subactivities_min_schema(result)

                if result is None or not _validate_subactivities_schema(result):
                    if attempt < max_retries:
                        wait = base_delay * (2 ** (attempt - 1))
                        time.sleep(wait)
                        continue
                    # If we failed with the current model, try switching models if available
                    if current_model_index < len(models_to_try) - 1:
                        print(f"⚠️ Switching model from {models_to_try[current_model_index]} to {models_to_try[current_model_index + 1]}")
                        current_model_index += 1
                        model = genai.GenerativeModel(
                            model_name=models_to_try[current_model_index],
                            generation_config={
                                "temperature": 0.10,
                                "max_output_tokens": 2048,
                            },
                        )
                        # Retry with new model immediately
                        continue
                        
                    end_of_data = True
                    break

                if result is None:
                    end_of_data = True
                    break

                subacts_page = result.get("subactividades", []) or []

                if page == 0:
                    total_declared = result.get("numero_subactividades")
                    if isinstance(total_declared, int) and total_declared > 0 and len(subacts_page) >= total_declared:
                        all_subacts.extend(subacts_page)
                        if use_cache:
                            _segment_page_cache[cache_key] = subacts_page
                        end_of_data = True
                        break

                if use_cache:
                    _segment_page_cache[cache_key] = subacts_page
                all_subacts.extend(subacts_page)

                if len(subacts_page) < page_size:
                    end_of_data = True
                    break

                start += page_size
                break

            except Exception as e:
                msg = str(e)
                print(f"Error generating content: {msg}")
                
                # If it's a model not found or similar error, switch model
                if ("404" in msg or "not found" in msg.lower() or "model" in msg.lower()) and current_model_index < len(models_to_try) - 1:
                     print(f"⚠️ Switching model from {models_to_try[current_model_index]} to {models_to_try[current_model_index + 1]}")
                     current_model_index += 1
                     model = genai.GenerativeModel(
                        model_name=models_to_try[current_model_index],
                        generation_config={
                            "temperature": 0.10,
                            "max_output_tokens": 2048,
                        },
                    )
                     continue

                if "quota" in msg.lower() or "429" in msg or "exceeded" in msg.lower():
                    if attempt < max_retries:
                        wait = base_delay * (2 ** (attempt - 1))
                        time.sleep(wait)
                        continue
                
                # If we are out of retries and have no subacts, re-raise to be caught by caller
                if attempt == max_retries and not all_subacts:
                    raise e
                
                return pd.DataFrame()

        if end_of_data:
            break

    subacts = _normalize_subactivities(all_subacts)
    
    try:
        subacts = _fix_dependencies_consistency(subacts)
    except NameError:
        pass

    df = pd.DataFrame(subacts)
    df["proceso"] = proceso_general
    df["fecha_generacion"] = datetime.now().isoformat()

    # Clasificar cada subactividad individualmente (modo híbrido)
    # NOTA: La reclasificación individual se ha eliminado porque el prompt de segmentación
    # ya solicita los tipos de actividad correctos (Operativa/Analítica/Cognitiva).
    # La función classify_single_activity original clasificaba en Valor/Desperdicio, lo cual no es compatible.
    
    return df


def generate_segmentation_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generar resumen estadístico del proceso segmentado
    """
    if df.empty:
        return {}

    total = len(df)
    tipos = df["tipo_actividad"].fillna("Indeterminado").astype(str).value_counts().to_dict() if "tipo_actividad" in df.columns else {}

    automatizable_col = df.get("automatizable", pd.Series([], dtype=str)).astype(str)
    total_automatizables = int((automatizable_col.str.lower() == "sí").sum() or (automatizable_col.str.lower() == "si").sum())
    total_posibles = int((automatizable_col.str.lower() == "posible").sum())
    total_no_automatizables = int((automatizable_col.str.lower() == "no").sum())

    valor_labels = {"Operativa", "Analítica", "Cognitiva"}
    valor_count = sum(v for k, v in tipos.items() if k in valor_labels)
    indeterminado_count = tipos.get("Indeterminado", 0)
    porcentaje_valor = (valor_count / total * 100) if total > 0 else 0
    porcentaje_indeterminadas = (indeterminado_count / total * 100) if total > 0 else 0

    recomendaciones_count = total_automatizables + total_posibles

    summary = {
        "total_subactividades": total,
        "tipos_actividad": tipos,
        "porcentaje_operativas": (tipos.get("Operativa", 0) / total * 100) if total > 0 else 0,
        "porcentaje_cognitivas": (tipos.get("Cognitiva", 0) / total * 100) if total > 0 else 0,
        "porcentaje_analiticas": (tipos.get("Analítica", 0) / total * 100) if total > 0 else 0,
        "porcentaje_colaborativa": 0,
        "porcentaje_decisoria": 0,
        "porcentaje_administrativa": 0,
        "porcentaje_espera_transición": 0,
        "total_automatizables": total_automatizables,
        "total_posibles": total_posibles,
        "total_no_automatizables": total_no_automatizables,
        "total_actividades": total,
        "valor": int(valor_count),
        "desperdicio": 0,
        "porcentaje_valor": porcentaje_valor,
        "porcentaje_desperdicio": 0,
        "indeterminadas": int(indeterminado_count),
        "porcentaje_indeterminadas": porcentaje_indeterminadas,
        "recomendaciones_count": int(recomendaciones_count),
        "tipos_desperdicio": {},
    }

    return summary


def export_segmentation_report(df: pd.DataFrame, summary: Dict[str, Any] = None, formato: str = "excel"):
  """
  Exportar reporte de segmentación incluyendo un resumen opcional.
  """
  if summary is None:
    summary = {}

  if formato == "excel":
    from io import BytesIO
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
      df.to_excel(writer, sheet_name="Subactividades", index=False)
      try:
        pd.DataFrame([summary]).to_excel(writer, sheet_name="Resumen", index=False)
      except Exception:
        from pandas import ExcelWriter
        pd.DataFrame([{"summary": str(summary)}]).to_excel(writer, sheet_name="Resumen", index=False)

    return output.getvalue()

  if formato == "csv":
    return df.to_csv(index=False).encode("utf-8")

  if formato == "json":
    result = {"subactividades": df.to_dict(orient="records"), "resumen": summary}
    return json.dumps(result, ensure_ascii=False, indent=2).encode("utf-8")

  return b""
