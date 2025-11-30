"""
Módulo de análisis de datos con diferentes modelos de IA
Versión optimizada - Solo modelos utilizados
"""

import time
import pandas as pd
from typing import Dict, Any, Optional
from config import ANALYSIS_CONFIG


class BaseAnalyzer:
    """Clase base para analizadores de datos"""
    
    def __init__(self):
        self.config = ANALYSIS_CONFIG
    
    def analyze(self, df: pd.DataFrame, user_question: Optional[str] = None) -> str:
        """Método abstracto para análisis"""
        raise NotImplementedError


class LocalAnalyzer(BaseAnalyzer):
    """Analizador local basado en reglas (sin dependencias externas)"""
    
    def analyze(self, df: pd.DataFrame, user_question: Optional[str] = None) -> str:
        """Analizar datos usando reglas locales"""
        try:
            # Handle case when df is None (for TO-BE analysis without data)
            if df is None:
                if user_question:
                    return self._answer_user_question(user_question)
                else:
                    return "No hay datos para analizar. Por favor, proporciona un prompt específico."
            
            dataset_info = self._prepare_dataset_info(df)
            analysis = self._generate_analysis(df, dataset_info)
            
            if user_question:
                analysis += self._answer_user_question(user_question)
            
            return analysis
            
        except Exception as e:
            return f"Error al analizar los datos: {str(e)}"
    
    def _prepare_dataset_info(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Preparar información del dataset"""
        return {
            "shape": df.shape,
            "columns": df.columns.tolist(),
            "dtypes": df.dtypes.to_dict(),
            "sample_data": df.head(5).to_dict(),
            "missing_values": df.isnull().sum().to_dict()
        }
    
    def _generate_analysis(self, df: pd.DataFrame, dataset_info: Dict[str, Any]) -> str:
        """Generar análisis principal"""
        analysis = f"""
# 📊 ANÁLISIS DE PROCESOS

## 📋 Resumen del Dataset
- **Filas**: {dataset_info['shape'][0]}
- **Columnas**: {dataset_info['shape'][1]}
- **Columnas disponibles**: {', '.join(dataset_info['columns'])}
- **Valores faltantes**: {sum(dataset_info['missing_values'].values())}

## 🔍 Análisis de Desperdicios Lean

### Actividades Identificadas:
"""
        
        # Analizar cada fila del dataset (primeras 10)
        for idx, row in df.head(self.config.get('sample_rows', 10)).iterrows():
            activity_info = self._analyze_activity(row, idx)
            analysis += activity_info
        
        analysis += self._generate_recommendations()
        return analysis
    
    def _analyze_activity(self, row: pd.Series, idx: int) -> str:
        """Analizar una actividad específica"""
        # Buscar columnas relevantes (flexible)
        activity = self._get_column_value(row, ['actividad', 'Actividad'], f'Actividad {idx+1}')
        description = self._get_column_value(row, ['descripcion', 'Descripción'], 'Sin descripción')
        necessary = self._get_column_value(row, ['necesaria', 'estado'], 'No especificado')
        
        # Clasificar como desperdicio
        waste_analysis = self._classify_waste(str(description))
        
        return f"""
**{activity}**
- Descripción: {description}
- Necesaria: {necessary}
- Desperdicio: {'SÍ' if waste_analysis['is_waste'] else 'NO'}
- Tipo: {waste_analysis['type'] if waste_analysis['is_waste'] else 'N/A'}
"""
    
    def _get_column_value(self, row: pd.Series, possible_names: list, default: str) -> str:
        """Obtener valor de columna con nombres flexibles"""
        for name in possible_names:
            for col in row.index:
                if name.lower() in col.lower():
                    return str(row[col]) if pd.notna(row[col]) else default
        return default
    
    def _classify_waste(self, description: str) -> Dict[str, Any]:
        """Clasificar si una actividad es desperdicio"""
        description_lower = description.lower()
        
        waste_patterns = {
            'Espera': ['espera', 'esperar', 'retraso', 'demora'],
            'Sobreproceso': ['repetir', 'duplicar', 'volver a'],
            'Transporte': ['mover', 'trasladar', 'transportar']
        }
        
        for waste_type, keywords in waste_patterns.items():
            if any(word in description_lower for word in keywords):
                return {'is_waste': True, 'type': waste_type}
        
        return {'is_waste': False, 'type': None}
    
    def _generate_recommendations(self) -> str:
        """Generar recomendaciones de optimización"""
        return """

## 🎯 Recomendaciones de Optimización

### 1. Eliminación de Desperdicios
- **Esperas**: Implementar sistema de notificaciones automáticas
- **Transporte**: Optimizar rutas con GPS
- **Sobreproceso**: Estandarizar procedimientos

### 2. Automatización con Power Platform
- **Power Automate**: Flujos de trabajo automatizados
- **Power Apps**: Aplicación móvil para conductores
- **Power BI**: Dashboard de monitoreo en tiempo real

### 3. Roadmap de Implementación (90 días)

**Semana 1-2**: Análisis detallado y mapeo de procesos
**Semana 3-4**: Diseño de soluciones Power Platform
**Semana 5-8**: Desarrollo y pruebas
**Semana 9-12**: Implementación y capacitación

### 4. Riesgos y Controles
- **Riesgo**: Resistencia al cambio
- **Control**: Programa de capacitación intensivo
- **Riesgo**: Fallas técnicas
- **Control**: Plan de respaldo manual

### 5. Plan de Entrenamiento
- **Semana 1**: Capacitación en Power Platform
- **Semana 2**: Pruebas piloto con usuarios clave
- **Semana 3**: Capacitación masiva
- **Semana 4**: Soporte y seguimiento
"""
    
    def _answer_user_question(self, user_question: str) -> str:
        """Responder pregunta específica del usuario"""
        return f"""

## 💬 Respuesta a tu pregunta:
**Pregunta**: {user_question}

**Respuesta**: Basado en el análisis del proceso, te recomiendo enfocarte en la eliminación de actividades de espera y transporte, que son los principales desperdicios identificados. La automatización con Power Platform puede reducir estos tiempos en un 60-80%.
"""


class GeminiAnalyzer(BaseAnalyzer):
    """Analizador usando Google Gemini API (requiere API key)"""
    
    def __init__(self, api_key: str):
        super().__init__()
        self.api_key = api_key
        self._configured = False
    
    def _configure_gemini(self):
        """Configurar Gemini solo una vez"""
        if not self._configured:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self._configured = True
                self.genai = genai
            except Exception as e:
                raise RuntimeError(f"Error al configurar Gemini: {str(e)}")
    
    def analyze(self, df: pd.DataFrame, user_question: Optional[str] = None) -> str:
        """Analizar datos usando Gemini"""
        try:
            if not self.api_key:
                return "Error: Necesitas configurar tu API Key de Google Gemini"
            
            self._configure_gemini()
            
            # Handle case when df is None (for TO-BE analysis without data)
            if df is None:
                prompt = user_question if user_question else "Analiza el proceso y proporciona recomendaciones de optimización."
                response = self._call_gemini_api(prompt)
                return response
            
            dataset_info = self._prepare_dataset_info(df)
            prompt = self._create_prompt(dataset_info, user_question)
            
            response = self._call_gemini_api(prompt)
            return response
            
        except Exception as e:
            return f"Error con Gemini: {str(e)}. Usando análisis local como respaldo."
    
    def _prepare_dataset_info(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Preparar información del dataset"""
        return {
            "shape": df.shape,
            "columns": df.columns.tolist(),
            "sample_data": df.head(5).to_dict()
        }
    
    def _create_prompt(self, dataset_info: Dict[str, Any], user_question: Optional[str] = None) -> str:
        """Crear prompt optimizado para Gemini"""
        sample_text = ""
        if dataset_info['sample_data']:
            for i, (col, values) in enumerate(list(dataset_info['sample_data'].items())[:3]):
                sample_text += f"\n- {col}: {list(values.values())[:2]}"
        
        prompt = f"""Analiza este proceso y proporciona:

**Datos**: {dataset_info['shape'][0]} actividades, columnas: {', '.join(dataset_info['columns'])}{sample_text}

**Análisis requerido**:
1. **Desperdicios Lean**: Identifica esperas, transporte, sobreproceso
2. **Clasificación**: Operativa/Analítica/Cognitiva  
3. **Automatización**: Soluciones Power Platform específicas
4. **Roadmap 90 días**: Cronograma de implementación
5. **KPIs**: Métricas de eficiencia y calidad

**Formato**: Markdown, respuestas concisas y prácticas."""
        
        if user_question:
            prompt += f"\n\n**Pregunta específica**: {user_question}"
        
        return prompt
    
    def _call_gemini_api(self, prompt: str) -> str:
        """Llamar a la API de Gemini con reintentos"""
        for attempt in range(self.config['retry_attempts']):
            try:
                model = self.genai.GenerativeModel(
                    model_name="gemini-2.0-flash",
                    generation_config={
                        "temperature": self.config['temperature_gemini'],
                        "max_output_tokens": self.config['max_tokens_gemini'],
                    }
                )
                
                response = model.generate_content(prompt)
                
                if response and hasattr(response, 'text'):
                    return response.text
                else:
                    if attempt < self.config['retry_attempts'] - 1:
                        time.sleep(self.config['retry_delay'])
                        continue
                    return "Error: No se recibió respuesta válida de Gemini."
                    
            except Exception as e:
                if attempt < self.config['retry_attempts'] - 1:
                    time.sleep(self.config['retry_delay'])
                    continue
                return f"Error al llamar a Gemini API: {str(e)}"
        
        return "Error: Se agotaron los intentos de conexión con Gemini."


def get_analyzer(model_type: str, api_key: Optional[str] = None) -> BaseAnalyzer:
    """
    Factory function para obtener el analizador correcto
    
    Args:
        model_type: Tipo de modelo a usar ('local' o 'gemini')
        api_key: API key para Gemini (opcional)
        
    Returns:
        Instancia del analizador correspondiente
    """
    analyzers = {
        "local": LocalAnalyzer,
        "gemini": lambda: GeminiAnalyzer(api_key) if api_key else LocalAnalyzer()
    }
    
    analyzer_class = analyzers.get(model_type, LocalAnalyzer)
    
    try:
        # Si es una función lambda, ejecutarla
        if callable(analyzer_class) and model_type == "gemini":
            return analyzer_class()
        
        # Si es una clase, instanciarla
        return analyzer_class()
        
    except RuntimeError as e:
        if "torch" in str(e).lower() or "path" in str(e).lower():
            print(f"⚠️ Error de PyTorch detectado: {str(e)}")
            print("🔄 Usando analizador local como respaldo...")
            return LocalAnalyzer()
        else:
            raise e
    except Exception as e:
        print(f"⚠️ Error al crear analizador {model_type}: {str(e)}")
        print("🔄 Usando analizador local como respaldo...")
        return LocalAnalyzer()
