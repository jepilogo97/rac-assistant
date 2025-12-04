/**
 * Global State Management - Zustand Store
 */
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

const useStore = create(
    persist(
        (set, get) => ({
            // Theme
            theme: 'light',
            toggleTheme: () => set((state) => ({ theme: state.theme === 'light' ? 'dark' : 'light' })),

            // API Key & Configuration
            apiKey: '',
            processContext: '',
            ragFiles: [],
            setApiKey: (key) => set({ apiKey: key }),
            setProcessContext: (context) => set({ processContext: context }),
            setRagFiles: (files) => set({ ragFiles: files }),

            // Upload state
            uploadedFile: null,
            processData: null,
            validationResult: null,
            setUploadedFile: (file) => set({ uploadedFile: file }),
            setProcessData: (data) => set({ processData: data }),
            setValidationResult: (result) => set({ validationResult: result }),

            // Validated data
            validatedData: null,
            setValidatedData: (data) => set({ validatedData: data }),

            // BPMN state
            bpmnXml: null,
            activities: [],
            setBpmnXml: (xml) => set({ bpmnXml: xml }),
            setActivities: (activities) => set({ activities }),

            // Classification state
            classifiedData: null,
            classificationSummary: null,
            setClassifiedData: (data) => set({ classifiedData: data }),
            setClassificationSummary: (summary) => set({ classificationSummary: summary }),

            // Segmentation state
            segmentedData: null,
            segments: null,
            setSegmentedData: (data) => set({ segmentedData: data }),
            setSegments: (segments) => set({ segments }),

            // TO-BE state
            tobeData: null,
            tobeProposals: null,
            sipocData: null,
            tobeBpmnXml: null,
            setTobeData: (data) => set({ tobeData: data }),
            setTobeProposals: (proposals) => set({ tobeProposals: proposals }),
            setSipocData: (data) => set({ sipocData: data }),
            setTobeBpmnXml: (xml) => set({ tobeBpmnXml: xml }),

            // TO-BE Comparison state
            tobeComparison: null,
            setTobeComparison: (data) => set({ tobeComparison: data }),

            // KPIs state
            kpisData: null,
            setKpisData: (data) => set({ kpisData: data }),

            // Loading states
            loading: {
                upload: false,
                validation: false,
                bpmn: false,
                classification: false,
                segmentation: false,
                tobe: false,
                kpis: false,
            },
            setLoading: (key, value) =>
                set((state) => ({ loading: { ...state.loading, [key]: value } })),

            // Clear all data (for new file upload)
            clearAllData: () => set({
                uploadedFile: null,
                processData: null,
                validationResult: null,
                validatedData: null,
                bpmnXml: null,
                activities: [],
                classifiedData: null,
                classificationSummary: null,
                segmentedData: null,
                segments: null,
                tobeData: null,
                tobeProposals: null,
                tobeComparison: null,
                sipocData: null,
                tobeBpmnXml: null,
                kpisData: null,
            }),
        }),
        {
            name: 'rac-assistant-storage',
            partialize: (state) => ({
                theme: state.theme,
                apiKey: state.apiKey,
                processContext: state.processContext,
            }),
        }
    )
);

export default useStore;
