/**
 * API Endpoints - All backend API calls
 */
import api from './api';

export const endpoints = {
    // Upload endpoints
    upload: {
        uploadFile: (file) => {
            const formData = new FormData();
            formData.append('file', file);
            return api.post('/api/upload', formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
            });
        },
        getExamples: () => api.get('/api/upload/example'),
    },

    // Validation endpoints
    validation: {
        validate: (data, apiKey) => api.post('/api/validate', { data, api_key: apiKey }),
    },

    // BPMN endpoints
    bpmn: {
        generate: (activities, config = {}) =>
            api.post('/api/bpmn/generate', { activities, ...config }),
        update: (activities, poolName) =>
            api.post('/api/bpmn/update', { activities, pool_name: poolName }),
        download: (xml) => api.post('/api/bpmn/download', xml),
        fromProcessData: (processData) =>
            api.post('/api/bpmn/from-process-data', processData),
    },

    // Classification endpoints
    classification: {
        classify: (data, apiKey) => api.post('/api/classify', { data, api_key: apiKey }),
        export: (classifiedData) => api.post('/api/classify/export', classifiedData, {
            responseType: 'blob',
        }),
        getCategories: () => api.get('/api/classify/categories'),
    },

    // Segmentation endpoints
    segmentation: {
        segment: (data, apiKey) => api.post('/api/segment', { data, api_key: apiKey }),
        export: (segmentedData) => api.post('/api/segment/export', segmentedData, {
            responseType: 'blob',
        }),
    },

    // TO-BE endpoints
    tobe: {
        generate: (classifiedData, segmentedData, apiKey, focusAreas, context) =>
            api.post('/api/tobe/generate', {
                classified_data: classifiedData,
                segmented_data: segmentedData,
                api_key: apiKey,
                focus_areas: focusAreas,
                contexto_proceso: context,
            }),
        compare: (asisData, tobeData) =>
            api.post('/api/tobe/compare', { asis_data: asisData, tobe_data: tobeData }),
        export: (data) =>
            api.post('/api/tobe/export', data, { responseType: 'blob' }),
    },

    // KPIs endpoints
    kpis: {
        analyze: (asisData, tobeData, classifiedData, apiKey) =>
            api.post('/api/kpis/analyze', {
                asis_data: asisData,
                tobe_data: tobeData,
                classified_data: classifiedData,
                api_key: apiKey,
            }),
        getDefinitions: () => api.get('/api/kpis/metrics-definitions'),
    },

    // Health check
    health: () => api.get('/api/health'),
};

export default endpoints;
