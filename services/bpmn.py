from xml.sax.saxutils import escape as _xml_esc
from typing import List, Dict, Any, Optional, Tuple
import streamlit as st
import streamlit.components.v1 as components
from json import dumps as _jdumps
import re
import unicodedata
import google.generativeai as genai

# =============================================================================
# UTILIDADES
# =============================================================================

def generate_short_summary(text: str, max_chars: int = 60) -> Optional[str]:
    """
    Usa Gemini (ya configurado previamente) para generar un resumen muy corto
    que sirva como nombre de la tarea BPMN.

    NO recibe api_key: se asume que genai.configure() ya fue llamado
    en otra parte (por ejemplo, initialize_gemini en gemini_integration.py).
    """
    if not text or len(text.strip()) < 10:
        return None

    try:
        # Usa el modelo recomendado
        model = genai.GenerativeModel("gemini-2.0-flash")
        prompt = (
            f"Genera un título corto (máx {max_chars} caracteres) que resuma "
            "la acción principal y el objeto de la actividad descrita. "
            "REGLAS OBLIGATORIAS:\n"
            "1. DEBE empezar con un VERBO EN INFINITIVO (ej: Crear, Revisar, Enviar).\n"
            "2. Debe tener coherencia gramatical y ser autoexplicativo.\n"
            "3. Evita artículos innecesarios al inicio.\n"
            "4. No uses punto final ni comillas.\n\n"
            f"Descripción: {text}\n\n"
            "Ejemplos:\n"
            "- Revisar solicitud de reembolso\n"
            "- Registrar datos del paciente\n"
            "- Validar documentos de ingreso\n"
            "- Enviar reporte semanal\n"
            "- Actualizar inventario en almacén"
        )
        response = model.generate_content(prompt)
        if not response or not getattr(response, "text", "").strip():
            return None
        return response.text.strip().split("\n")[0][:max_chars]
    except Exception as e:
        print(f"[WARN] Gemini short summary failed: {e}")
        return None


def generate_compact_name(
    description: str,
    activity_name: str = "",
    max_words: int = 6,
    max_chars: int = 60
) -> str:
    """
    Generar nombre compacto y legible para actividad BPMN
    SOLO a partir de la descripción (el nombre original solo se usa como fallback).
    """
    def strip_accents(s: str) -> str:
        return ''.join(
            c for c in unicodedata.normalize('NFKD', s)
            if not unicodedata.combining(c)
        )

    def title_es(s: str) -> str:
        return " ".join(w.capitalize() for w in s.split())

    def limit_len(s: str) -> str:
        words = s.split()
        if len(words) > max_words:
            s = " ".join(words[:max_words])
        if len(s) > max_chars:
            s = s[:max_chars].rstrip()
        return s

    # Validar entradas vacías
    if not isinstance(description, str) or not description.strip():
        base = activity_name.strip() if isinstance(activity_name, str) else ""
        return base or "Actividad"

    t = description.strip()
    
    # Limpiar numeración y símbolos
    t = re.sub(r"^\s*[\-\*\u2022]?\s*\d+[\.\)\-:]\s*", "", t)
    t = re.sub(r"\b\d+[\.\)\-:]*\s*", " ", t)
    t = re.sub(r"[•·✓✔✅\[\]\(\)\{\}#*_~<>|]", " ", t)
    
    # Eliminar colas poco informativas
    tails = [
        r"por correo electr[oó]nico.*",
        r"v[ií]a correo.*",
        r"por whatsapp.*",
        r"en (el )?sistema.*"
    ]
    for pat in tails:
        t = re.sub(rf"\s+{pat}$", "", t, flags=re.IGNORECASE).strip()

    t_lower = t.lower()
    
    # Nominalización de verbos
    verb_nominal = {
        "recibir": "Recepción de",
        "recepcionar": "Recepción de",
        "leer": "Lectura de",
        "revisar": "Revisión de",
        "validar": "Validación de",
        "verificar": "Verificación de",
        "procesar": "Proceso de",
        "analizar": "Análisis de",
        "generar": "Generación de",
        "crear": "Creación de",
        "enviar": "Envío de",
        "descargar": "Descarga de",
        "aprobar": "Aprobación de",
        "rechazar": "Rechazo de"
    }
    
    head = strip_accents(t_lower.split()[0]) if t_lower else ""
    
    # Caso especial: "recepción y lectura de"
    if t_lower.startswith("recepción y lectura de "):
        core = t_lower
        core = re.sub(r"\bde\s+(de|la|el|los|las)\b", "de", core)
        result = title_es(limit_len(core))
        return result if result else (activity_name or "Actividad")
    
    # Si empieza con verbo de la lista
    if head in verb_nominal:
        resto = t_lower[len(t_lower.split()[0]):].strip()
        resto = re.sub(r"^(la|el|los|las|un|una|unos|unas)\s+", "", resto)
        core = f"{verb_nominal[head]} {resto}".strip()
        core = re.sub(r"\bde\s+(de|la|el|los|las)\b", "de", core)
        core = re.sub(r"\s+", " ", core).strip()
        result = title_es(limit_len(core))
        return result if result else (activity_name or "Actividad")
    
    # Sin verbo: tomar sustantivos clave
    stopwords = {
        "de","la","el","en","con","para","por","del","las","los","una","un",
        "y","o","u","al","lo","su","sus","a","que","se"
    }
    tokens = [w.strip(".,;:!?") for w in t_lower.split()]
    content = [w for w in tokens if w and w not in stopwords and len(w) > 2]
    
    if content:
        core = " ".join(content[:max_words])
        result = title_es(limit_len(core))
        return result if result else (activity_name or "Actividad")
    
    # Fallback
    base = activity_name.strip() if isinstance(activity_name, str) else ""
    return base or "Actividad"


def _esc(s: Any) -> str:
    """Escapar caracteres especiales XML"""
    return _xml_esc(str(s or ""))


def _id(prefix: str, i: int) -> str:
    """Generar ID único"""
    return f"{prefix}_{i}"


def _dim_for(kind: str) -> Tuple[int, int]:
    """Obtener dimensiones óptimas para cada tipo de elemento BPMN"""
    dimensions = {
        "startEvent": (36, 36),
        "endEvent": (36, 36),
        "intermediateThrowEvent": (36, 36),
        "intermediateCatchEvent": (36, 36),
        "boundaryEvent": (36, 36),
        "exclusiveGateway": (50, 50),
        "task": (160, 90),
        "userTask": (160, 90),
        "serviceTask": (160, 90),
        "sendTask": (160, 90),
        "receiveTask": (160, 90),
        "subProcess": (180, 100),
    }
    return dimensions.get(kind, (140, 80))


# =============================================================================
# BUILDER PRINCIPAL (XML BPMN 2.0)
# =============================================================================

def build_bpmn_xml_advanced(
    *,
    activities: List[Dict[str, Any]],
    flows: Optional[List[Dict[str, str]]] = None,
    pool_name: str = "Proceso",
    use_lanes: bool = True,
    decisions: Optional[List[Dict[str, Any]]] = None,
    timers: Optional[List[Dict[str, Any]]] = None,
    messages: Optional[List[Dict[str, Any]]] = None,
    subprocesses: Optional[List[Dict[str, Any]]] = None,
    add_di: bool = True,
    show_times: bool = True,
) -> str:
    """Generar XML BPMN 2.0 con layout optimizado"""
    flows = flows or []
    decisions = decisions or []
    timers = timers or []
    messages = messages or []
    subprocesses = subprocesses or []

    # 🔹 Filtrar gateways tipo "Proceso válido"
    clean_decisions: List[Dict[str, Any]] = []
    for g in decisions:
        name = g.get("name") or ""
        name_norm = str(name).lower().replace("¿", "").replace("?", "").replace("á", "a").strip()
        if "proceso valido" in name_norm:
            continue
        clean_decisions.append(g)

    act_by_id = {a["id"]: a for a in activities}

    # ==============================================================  
    # Normalización de etiquetas (SOLO DESCRIPTION → nombre compacto)
    # ==============================================================

    for a in activities:
        desc_raw = (a.get("description") or "").strip()
        name_raw = (a.get("name") or "").strip()

        # 1️⃣ Intentar resumen corto con Gemini (si ya está configurado)
        compact_label = None
        if desc_raw:
            try:
                compact_label = generate_short_summary(desc_raw, max_chars=60)
            except Exception as e:
                print(f"[WARN] Gemini resumen falló: {e}")

        # 2️⃣ Fallback: heurística local
        if not compact_label:
            compact_label = generate_compact_name(
                description=desc_raw,
                activity_name=name_raw,
                max_words=6,
                max_chars=60
            )

        # 3️⃣ Añadir tiempos si aplica
        if show_times:
            if a.get("time_standard"):
                compact_label += f"\n⏱ {a['time_standard']:.0f} min"
            elif a.get("time_avg"):
                compact_label += f"\n⏱ ~{a['time_avg']:.0f} min"

        a["label"] = compact_label

    # ==============================================================  
    # XML HEADER
    # ==============================================================  
    out = []
    out.append('<?xml version="1.0" encoding="UTF-8"?>')
    out.append('<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL"')
    out.append('  xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"')
    out.append('  xmlns:di="http://www.omg.org/spec/DD/20100524/DI"')
    out.append('  xmlns:dc="http://www.omg.org/spec/DD/20100524/DC"')
    out.append('  id="Definitions_1" targetNamespace="http://example.com/bpmn">')

    collab_id = "Collab_1"
    proc_id = "Process_1"
    out.append(f'  <collaboration id="{collab_id}">')
    out.append(f'    <participant id="Participant_1" processRef="{proc_id}" name="{_esc(pool_name)}"/>')
    out.append('  </collaboration>')
    out.append(f'  <process id="{proc_id}" isExecutable="false">')

    # ==============================================================  
    # LANES
    # ==============================================================  
    lane_ids, lane_order = {}, {}
    if use_lanes:
        out.append('    <laneSet id="LaneSet_1">')
        resp_map, resp_unique = {}, []
        for a in activities:
            r = a.get("responsible") or "Sin asignar"
            if r not in resp_unique:
                resp_unique.append(r)
            resp_map.setdefault(r, []).append(a["id"])
        for i, resp in enumerate(resp_unique, 1):
            lid = _id("Lane", i)
            lane_ids[resp] = lid
            lane_order[resp] = i - 1
            out.append(f'      <lane id="{lid}" name="{_esc(resp)}">')
            for aid in resp_map[resp]:
                out.append(f'        <flowNodeRef>{aid}</flowNodeRef>')
            out.append('      </lane>')
        out.append('    </laneSet>')

    # ==============================================================  
    # START / END EVENTS
    # ==============================================================  
    start_id, end_id = "StartEvent_1", "EndEvent_1"
    out.append(f'    <startEvent id="{start_id}" name="Inicio"/>')
    out.append(f'    <endEvent id="{end_id}" name="Fin"/>')

    # ==============================================================  
    # TAREAS
    # ==============================================================  
    di_nodes, di_edges = [], []

    def _push_shape(el_id: str, kind: str, x: int, y: int):
        w, h = _dim_for(kind)
        di_nodes.append({"id": el_id, "kind": kind, "x": x, "y": y, "w": w, "h": h})

    for a in activities:
        tid = a["id"]
        ttype = "serviceTask" if a.get("automated") else "userTask"
        out.append(f'    <{ttype} id="{tid}" name="{_esc(a["label"])}">')

        # Documentación: descripción completa + tiempos detallados
        doc_parts = []
        if a.get("description"):
            doc_parts.append(str(a["description"]))
        if show_times:
            tinfo = []
            if a.get("time_standard"):
                tinfo.append(f"⏱ Tiempo estándar: {a['time_standard']:.1f} min")
            if a.get("time_avg"):
                tinfo.append(f"📊 Tiempo promedio: {a['time_avg']:.1f} min")
            if a.get("time_min"):
                tinfo.append(f"⚡ Tiempo mínimo: {a['time_min']:.1f} min")
            if a.get("time_max"):
                tinfo.append(f"🔻 Tiempo máximo: {a['time_max']:.1f} min")
            if tinfo:
                doc_parts.append(" | ".join(tinfo))
        if doc_parts:
            out.append(f'      <documentation>{_esc(" || ".join(doc_parts))}</documentation>')

        out.append(f'    </{ttype}>')

    # ==============================================================  
    # FLOWS
    # ==============================================================  
    flow_i = 1

    def _push_flow(src, dst, label=None):
        nonlocal flow_i
        fid = _id("Flow", flow_i)
        flow_i += 1
        if label:
            lbl = label.lower().replace("¿", "").replace("?", "").replace("á", "a").strip()
            if "proceso valido" in lbl:
                label = None
        if label:
            out.append(f'    <sequenceFlow id="{fid}" sourceRef="{src}" targetRef="{dst}" name="{_esc(label)}"/>')
        else:
            out.append(f'    <sequenceFlow id="{fid}" sourceRef="{src}" targetRef="{dst}"/>')
        di_edges.append({"id": fid, "source": src, "target": dst})

    if not flows and activities:
        _push_flow("StartEvent_1", activities[0]["id"])
        for i in range(len(activities) - 1):
            _push_flow(activities[i]["id"], activities[i + 1]["id"])
        _push_flow(activities[-1]["id"], "EndEvent_1")
    for f in flows:
        _push_flow(f["source"], f["target"], f.get("name"))

    out.append("  </process>")

    # ==============================================================  
    # DIAGRAMA BPMN-DI
    # ==============================================================  
    if add_di:
        X0, Y0, DX, DY = 200, 180, 350, 280
        LANE_PAD = 70
        _push_shape("StartEvent_1", "startEvent", X0 - 100, Y0)
        max_x = X0 + DX * max(1, len(activities))
        _push_shape("EndEvent_1", "endEvent", max_x + 100, Y0)

        lane_count = {}
        for i, a in enumerate(activities, 1):
            resp = a.get("responsible") or "Sin asignar"
            lane_idx = lane_order.get(resp, 0)
            lane_count[resp] = lane_count.get(resp, 0) + 1
            x, y = X0 + DX * i, Y0 + lane_idx * DY + LANE_PAD
            kind = "serviceTask" if a.get("automated") else "userTask"
            _push_shape(a["id"], kind, x, y)

        out.append('  <bpmndi:BPMNDiagram id="BPMNDiagram_1">')
        out.append('    <bpmndi:BPMNPlane id="BPMNPlane_1" bpmnElement="Collab_1">')

        total_lanes = max(1, len(lane_order))
        pool_w, pool_h = max_x + 250, 100 + total_lanes * DY
        out.append(f'      <bpmndi:BPMNShape id="Participant_1_di" bpmnElement="Participant_1" isHorizontal="true">')
        out.append(f'        <dc:Bounds x="50" y="50" width="{pool_w}" height="{pool_h}"/>')
        out.append('      </bpmndi:BPMNShape>')

        if use_lanes:
            for resp, idx in lane_order.items():
                lid = lane_ids[resp]
                lane_y = 70 + idx * DY
                out.append(f'      <bpmndi:BPMNShape id="{lid}_di" bpmnElement="{lid}" isHorizontal="true">')
                out.append(f'        <dc:Bounds x="80" y="{lane_y}" width="{pool_w-60}" height="{DY-40}"/>')
                out.append('      </bpmndi:BPMNShape>')

        for n in di_nodes:
            out.append(f'      <bpmndi:BPMNShape id="{n["id"]}_di" bpmnElement="{n["id"]}">')
            out.append(f'        <dc:Bounds x="{n["x"]}" y="{n["y"]}" width="{n["w"]}" height="{n["h"]}"/>')
            out.append('      </bpmndi:BPMNShape>')

        for e in di_edges:
            out.append(f'      <bpmndi:BPMNEdge id="{e["id"]}_di" bpmnElement="{e["id"]}">')
            s = next((n for n in di_nodes if n["id"] == e["source"]), None)
            t = next((n for n in di_nodes if n["id"] == e["target"]), None)
            if s and t:
                sx, sy, tx, ty = s["x"] + s["w"], s["y"] + s["h"] // 2, t["x"], t["y"] + t["h"] // 2
                out.append(f'        <di:waypoint x="{sx}" y="{sy}"/>')
                if abs(sy - ty) > 60:
                    mid_x = (sx + tx) // 2
                    out.append(f'        <di:waypoint x="{mid_x}" y="{sy}"/>')
                    out.append(f'        <di:waypoint x="{mid_x}" y="{ty}"/>')
                out.append(f'        <di:waypoint x="{tx}" y="{ty}"/>')
            else:
                out.append('        <di:waypoint x="150" y="150"/>')
                out.append('        <di:waypoint x="300" y="200"/>')
            out.append('      </bpmndi:BPMNEdge>')
        out.append('    </bpmndi:BPMNPlane>')
        out.append('  </bpmndi:BPMNDiagram>')

    out.append('</definitions>')
    return "\n".join(out)


# =============================================================================
# RENDERER CON BPMN-JS (STREAMLIT) - VIEWER (SOLO LECTURA)
# =============================================================================

def render_bpmn_xml(xml_str: str, height: int = 800, key: str = "bpmn_viewer"):
    """
    Renderizar diagrama BPMN usando BpmnNavigatedViewer (SOLO LECTURA)
    con zoom y paneo directo con el mouse
    """
    safe_xml = _jdumps(xml_str)

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            #{key}_canvas {{
                height: {height}px;
                border: 2px solid #1ABC9C;
                border-radius: 12px;
                background: #FAFAFA;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                cursor: grab;
            }}
            #{key}_canvas:active {{
                cursor: grabbing;
            }}
            .error {{
                color: #E74C3C;
                padding: 20px;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                font-size: 14px;
            }}
        </style>
    </head>
    <body>
        <div id="{key}_canvas"></div>

        <!-- Usamos NavigatedViewer para zoom/pan -->
        <script src="https://unpkg.com/bpmn-js@11.5.0/dist/bpmn-navigated-viewer.development.js"></script>
        <script>
            (function() {{
                const xml = {safe_xml};

                const viewer = new BpmnJS({{ 
                    container: '#{key}_canvas',
                    height: {height}
                }});

                viewer.importXML(xml)
                    .then(() => {{
                        const canvas = viewer.get('canvas');
                        canvas.zoom('fit-viewport', 'auto');
                    }})
                    .catch(err => {{
                        const el = document.getElementById('{key}_canvas');
                        el.innerHTML = '<div class="error">❌ Error al cargar BPMN: ' + 
                                      (err?.message || err) + '</div>';
                        console.error('BPMN Error:', err);
                    }});
            }})();
        </script>
    </body>
    </html>
    """

    components.html(html, height=height + 20, scrolling=True)


# =============================================================================
# RENDERER EDITABLE CON BPMN-JS MODELER
# =============================================================================

def render_bpmn_editable(xml_str: str, height: int = 800, key: str = "bpmn_modeler"):
    """
    Renderizar diagrama BPMN EDITABLE usando BpmnJS Modeler
    Permite:
    - Arrastrar actividades
    - Cambiar conexiones
    - Editar propiedades
    - Guardar/Exportar cambios
    """
    safe_xml = _jdumps(xml_str)

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            #{key}_canvas {{
                height: {height}px;
                border: 2px solid #3498DB;
                border-radius: 12px;
                background: #FAFAFA;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }}

            .controls {{
                margin-bottom: 10px;
                padding: 12px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 8px;
                display: flex;
                gap: 10px;
                flex-wrap: wrap;
                align-items: center;
            }}

            .btn {{
                padding: 8px 16px;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                font-size: 14px;
            }}

            .info-banner {{
                background: #D6EAF8;
                border-left: 4px solid #3498DB;
                padding: 10px 15px;
                margin-bottom: 10px;
                border-radius: 6px;
                font-size: 13px;
                color: #21618C;
            }}

            .status {{
                padding: 4px 10px;
                border-radius: 6px;
                font-size: 12px;
            }}

            .status.saved {{
                background: #D4EFDF;
                color: #1D8348;
            }}

            .status.modified {{
                background: #FADBD8;
                color: #922B21;
            }}
        </style>
    </head>
    <body>
        <div class="info-banner">
            ✏️ <strong>Modo Edición:</strong> Puedes arrastrar actividades y cambiar conexiones.
            Los cambios visuales se pueden descargar pero no se guardan automáticamente en la tabla.
        </div>

        <div class="controls">
            <button class="btn btn-primary" onclick="downloadXML()">
                💾 Descargar XML
            </button>
            <button class="btn btn-secondary" onclick="zoomIn()">
                🔍+ Zoom In
            </button>
            <button class="btn btn-secondary" onclick="zoomOut()">
                🔍- Zoom Out
            </button>
            <button class="btn btn-secondary" onclick="zoomFit()">
                📐 Ajustar
            </button>
            <button class="btn btn-danger" onclick="resetDiagram()">
                🔄 Resetear
            </button>
            <div id="status" class="status saved">✅ Sin cambios</div>
        </div>

        <div id="{key}_canvas"></div>

        <!-- BPMN-JS Modeler (editable) -->
        <script src="https://unpkg.com/bpmn-js@11.5.0/dist/bpmn-modeler.development.js"></script>
        <script>
            (function() {{
                const xml = {safe_xml};
                let hasChanges = false;
                let modeler;

                const statusEl = document.getElementById('status');

                modeler = new BpmnJS({{
                    container: '#{key}_canvas',
                    height: {height},
                    keyboard: {{ bindTo: document }}
                }});

                modeler.importXML(xml)
                    .then(() => {{
                        const canvas = modeler.get('canvas');
                        canvas.zoom('fit-viewport', 'auto');

                        modeler.on('commandStack.changed', () => {{
                            hasChanges = true;
                            statusEl.className = 'status modified';
                            statusEl.textContent = '⚠️ Cambios sin guardar';
                        }});
                    }})
                    .catch(err => {{
                        const el = document.getElementById('{key}_canvas');
                        el.innerHTML = '<div class="error">❌ Error al cargar BPMN: ' + (err && err.message ? err.message : err) + '</div>';
                        console.error('BPMN Error:', err);
                    }});

                window.downloadXML = function() {{
                    modeler.saveXML({{ format: true }})
                        .then(function(result) {{
                            const xml = result.xml;
                            const blob = new Blob([xml], {{ type: 'application/xml' }});
                            const url = URL.createObjectURL(blob);
                            const a = document.createElement('a');
                            a.href = url;
                            a.download = 'diagrama_editado.bpmn';
                            document.body.appendChild(a);
                            a.click();
                            document.body.removeChild(a);
                            URL.revokeObjectURL(url);

                            statusEl.className = 'status saved';
                            statusEl.textContent = '✅ XML descargado';
                            setTimeout(() => {{
                                statusEl.textContent = '✅ Sin cambios';
                            }}, 2000);
                        }})
                        .catch(err => {{
                            alert('❌ Error al exportar: ' + err.message);
                        }});
                }};

                window.zoomIn = function() {{
                    const canvas = modeler.get('canvas');
                    canvas.zoom(canvas.zoom() + 0.1);
                }};

                window.zoomOut = function() {{
                    const canvas = modeler.get('canvas');
                    const currentZoom = canvas.zoom();
                    if (currentZoom > 0.2) {{
                        canvas.zoom(currentZoom - 0.1);
                    }}
                }};

                window.zoomFit = function() {{
                    const canvas = modeler.get('canvas');
                    canvas.zoom('fit-viewport', 'auto');
                }};

                window.resetDiagram = function() {{
                    if (confirm('¿Resetear todos los cambios?')) {{
                        modeler.importXML(xml)
                            .then(() => {{
                                const canvas = modeler.get('canvas');
                                canvas.zoom('fit-viewport', 'auto');
                                hasChanges = false;
                                statusEl.className = 'status saved';
                                statusEl.textContent = '✅ Diagrama reseteado';

                                setTimeout(() => {{
                                    statusEl.textContent = '✅ Sin cambios';
                                }}, 2000);
                            }});
                    }}
                }};

                // Advertencia al salir sin guardar
                window.addEventListener('beforeunload', (e) => {{
                    if (hasChanges) {{
                        e.preventDefault();
                        e.returnValue = 'Tienes cambios sin guardar';
                    }}
                }});

                // Enviar XML editado al backend cuando se guarda
                window.saveToBackend = function() {{
                    modeler.saveXML({{ format: true }})
                        .then(function(result) {{
                            const xml = result.xml;
                            if (window.Streamlit) {{
                                window.Streamlit.setComponentValue(xml);
                            }}
                            // Actualizar estado visual y variable
                            hasChanges = false;
                            statusEl.className = 'status saved';
                            statusEl.textContent = '✅ Sin cambios';
                        }});
                }};

                // Agregar botón para guardar en backend
                const guardarBtn = document.createElement('button');
                guardarBtn.textContent = '💾 Guardar';
                guardarBtn.className = 'btn btn-success';
                guardarBtn.onclick = window.saveToBackend;
                document.querySelector('.controls').appendChild(guardarBtn);
            }})();
        </script>
    </body>
    </html>
    """
    
    components.html(html, height=height + 100, scrolling=True)


# =============================================================================
# HELPER: CONVERTIR DESDE PROCESS_DATA
# =============================================================================

def to_builder_inputs_from_process_data(process_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convertir estructura de proceso al formato del builder BPMN.
    🔹 NO usa compact_name de Gemini.
    🔹 Propaga descripción, responsable y tiempos.
    """
    acts_in = []
    
    for a in process_data.get("activities", []):
        acts_in.append({
            "id": a.get("id"),
            "name": a.get("name") or a.get("description") or a.get("id"),
            "description": a.get("description") or a.get("full_description") or "",
            "responsible": a.get("responsible") or "Sin asignar",
            "automated": bool(a.get("automated")),
            "time_standard": a.get("time_standard"),
            "time_avg": a.get("time_avg"),
            "time_min": a.get("time_min"),
            "time_max": a.get("time_max"),
        })

    # Generar flujos secuenciales automáticos
    flows_in = []
    if len(acts_in) >= 2:
        for i in range(len(acts_in) - 1):
            flows_in.append({
                "source": acts_in[i]["id"],
                "target": acts_in[i + 1]["id"]
            })

    return {
        "activities": acts_in,
        "flows": flows_in,
        "decisions": [],
        "timers": [],
        "messages": [],
        "subprocesses": [],
    }
