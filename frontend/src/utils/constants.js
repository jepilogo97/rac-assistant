/**
 * Constants used throughout the application
 */

export const APP_NAME = 'RAC Assistant';
export const APP_VERSION = '2.0.0';

export const TABS = [
    { id: 'upload', label: '📂 Carga de Datos', icon: 'Upload' },
    { id: 'process', label: '📊 Diagrama de Flujo', icon: 'GitBranch' },
    { id: 'classifier', label: '🎯 A. Desperdicios', icon: 'Tags' },
    { id: 'segmenter', label: '🧠 A. Actividades', icon: 'Layers' },
    { id: 'tobe', label: '🚀 Proceso Sugerido', icon: 'Target' },
    { id: 'kpis', label: '📈 KPIs y Métricas', icon: 'BarChart3' },
];

export const FILE_CONFIG = {
    maxSize: 10 * 1024 * 1024, // 10MB
    acceptedFormats: ['.xlsx', '.xls'],
    expectedColumns: [
        'Estado',
        'Actividad',
        'Descripción',
        'Cargo que ejecuta la tarea',
        'Tarea Automatizada',
        'No. Colaboradores que ejecutan la tarea',
        'Volumen Promedio Mensual',
        'Tiempo Menor',
        'Tiempo Mayor',
        'Tiempo Promedio',
        'Tiempo Estándar',
    ],
};

export const WASTE_CATEGORIES = [
    { id: 'transporte', name: 'Transporte', color: '#ef4444' },
    { id: 'inventario', name: 'Inventario', color: '#f59e0b' },
    { id: 'movimiento', name: 'Movimiento', color: '#eab308' },
    { id: 'espera', name: 'Espera', color: '#84cc16' },
    { id: 'sobreprocesamiento', name: 'Sobreprocesamiento', color: '#22c55e' },
    { id: 'sobreproduccion', name: 'Sobreproducción', color: '#10b981' },
    { id: 'defectos', name: 'Defectos', color: '#14b8a6' },
    { id: 'talento', name: 'Talento no utilizado', color: '#06b6d4' },
    { id: 'ninguno', name: 'Sin desperdicio', color: '#3b82f6' },
];

export const API_MODELS = {
    gemini: 'Google Gemini 2.0',
};
