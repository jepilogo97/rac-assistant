/**
 * TOBE Page - TO-BE Process Generation and Comparison
 */
import { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Play, GitCompare, TrendingUp, Lightbulb, RotateCcw, Download } from 'lucide-react';
import toast from 'react-hot-toast';
import useStore from '../store';
import endpoints from '../services/endpoints';
import Card, { CardHeader, CardTitle, CardContent } from '../components/common/Card';
import Button from '../components/common/Button';
import ProgressBar from '../components/common/ProgressBar';
import { formatNumber, formatPercentage, formatTime } from '../utils/formatters';
import EmptyState from '../components/common/EmptyState';
import BpmnModeler from 'bpmn-js/lib/Modeler';

export default function TOBEPage() {
    const {
        processData,
        validatedData,
        classifiedData,
        segmentedData,
        tobeData,
        tobeProposals,
        setTobeData,
        setTobeProposals,
        sipocData,
        setSipocData,
        tobeBpmnXml,
        setTobeBpmnXml,
        tobeComparison,
        setTobeComparison,
        loading,
        setLoading,
        apiKey,
        processContext
    } = useStore();

    const [progress, setProgress] = useState(0);
    const bpmnContainerRef = useRef(null);

    const handleGenerateTOBE = async () => {
        if (!processData && !validatedData) {
            toast.error('Debes cargar un archivo primero');
            return;
        }

        if (!classifiedData && !segmentedData) {
            toast.error('Debes tener datos clasificados o segmentados para generar el TO-BE');
            return;
        }

        if (!apiKey) {
            toast.error('Por favor configura tu API Key en el menú de Configuración');
            return;
        }

        if (!processContext || !processContext.trim()) {
            toast.error('Por favor configura el Contexto del Proceso en el menú de Configuración');
            return;
        }

        setLoading('tobe', true);
        setProgress(0);

        try {
            // Simulate progress
            const progressInterval = setInterval(() => {
                setProgress(prev => Math.min(prev + 10, 90));
            }, 700);

            const result = await endpoints.tobe.generate(
                classifiedData,
                segmentedData,
                apiKey,
                null,
                processContext // Pass global context
            );

            clearInterval(progressInterval);
            setProgress(100);

            if (result.success) {
                setTobeData(result.tobe_data || result.proposals);
                setTobeProposals(result.proposals);
                console.log('SIPOC Data received:', result.sipoc);
                if (result.sipoc) {
                    setSipocData(result.sipoc);
                }
                toast.success('Proceso TO-BE generado exitosamente');

                // Generate comparison
                await handleCompare(result.tobe_data || result.proposals);
            }
        } catch (error) {
            toast.error(error.message || 'Error al generar proceso TO-BE');
        } finally {
            setLoading('tobe', false);
            setTimeout(() => setProgress(0), 1000);
        }
    };

    const generateBpmnXml = async (proposals, segmentedActivities) => {
        console.log('generateBpmnXml called with:', { proposals, segmentedActivities });
        if (!proposals || proposals.length === 0) return null;

        try {
            // Filter out eliminated activities and merge with segmented data
            const activeProposals = proposals.filter(p => p.accion !== 'Eliminada');
            console.log('Active proposals:', activeProposals.length);

            // Transform to the same format as AS-IS (Process.jsx format)
            const activitiesData = activeProposals.map((proposal, index) => {
                // Find corresponding segmented activity
                const segmentedActivity = segmentedActivities?.find(a => a.id === proposal.id) || {};

                return {
                    id: `activity_${index + 1}`,
                    name: proposal.nombre || `Actividad ${index + 1}`,
                    description: proposal.descripcion || '',
                    responsible: segmentedActivity['Cargo que ejecuta la tarea'] || segmentedActivity.responsable || 'Sin asignar',
                    time: proposal.tiempo_mejorado_minutos || proposal.tiempo_original_minutos || 0,
                    automated: false
                };
            });

            // Call backend BPMN generation endpoint with the same format as AS-IS
            const result = await endpoints.bpmn.generate(activitiesData, {
                pool_name: 'Proceso TO-BE Optimizado',
                use_lanes: true,
                show_times: true
            });

            console.log('Calling BPMN endpoint with activities:', activitiesData);
            console.log('BPMN generation result:', result);
            console.log('XML preview:', result.xml?.substring(0, 500));
            return result.xml;
        } catch (error) {
            console.error('Error generating BPMN:', error);
            console.error('Error details:', error.response?.data);
            toast.error('Error al generar el diagrama BPMN: ' + (error.response?.data?.detail || error.message));
            return null;
        }
    };

    const handleExport = async () => {
        if (!segmentedData || !tobeProposals) {
            toast.error('No hay datos para exportar');
            return;
        }

        try {
            const mergedData = segmentedData.map((item, index) => {
                // Try to match by ID, fallback to index
                const proposal = tobeProposals.find(p => p.id === item.id) || tobeProposals[index] || {};

                return {
                    ...item,
                    '--- TO-BE ---': '', // Separator
                    'Acción Propuesta': proposal.accion || 'Mantenida',
                    'Descripción Mejora': proposal.descripcion || '',
                    'Justificación Mejora': proposal.justificacion || '',
                    'Tiempo Mejorado (min)': proposal.tiempo_mejorado_minutos,
                    'Reducción (%)': proposal.reduccion_tiempo_porcentaje
                };
            });

            const blob = await endpoints.tobe.export(mergedData);
            const url = window.URL.createObjectURL(new Blob([blob]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', 'proceso_tobe_completo.xlsx');
            document.body.appendChild(link);
            link.click();
            link.parentNode.removeChild(link);
            toast.success('Archivo exportado exitosamente');
        } catch (error) {
            console.error('Export error:', error);
            toast.error('Error al exportar el archivo');
        }
    };

    const handleCompare = async (tobeData) => {
        try {
            // Use segmentedData as AS-IS data if available, otherwise classifiedData
            const asisData = segmentedData || classifiedData;

            if (!asisData || asisData.length === 0) {
                console.warn('No AS-IS data available for comparison');
                return;
            }

            const result = await endpoints.tobe.compare(asisData, tobeData);
            setTobeComparison(result);
        } catch (error) {
            console.error('Error generating comparison:', error);
            toast.error('Error al generar métricas de comparación');
        }
    };

    // Generate and render BPMN diagram
    useEffect(() => {
        console.log('BPMN useEffect triggered:', { tobeProposals, segmentedData, tobeBpmnXml });

        let modeler = null;

        const generateAndRenderBpmn = async () => {
            // If we already have XML in store, just render it
            if (tobeBpmnXml && bpmnContainerRef.current) {
                modeler = new BpmnModeler({
                    container: bpmnContainerRef.current,
                    keyboard: { bindTo: document }
                });

                try {
                    await modeler.importXML(tobeBpmnXml);
                    const canvas = modeler.get('canvas');
                    setTimeout(() => {
                        canvas.zoom('fit-viewport', 'auto');
                    }, 100);
                } catch (err) {
                    console.error('Error rendering BPMN from store:', err);
                }
                return;
            }

            // Otherwise, generate new XML if we have proposals
            if (tobeProposals && tobeProposals.length > 0 && segmentedData) {
                const xml = await generateBpmnXml(tobeProposals, segmentedData);
                console.log('Generated BPMN XML:', xml ? 'Success' : 'Failed');

                if (xml) {
                    setTobeBpmnXml(xml);

                    if (bpmnContainerRef.current) {
                        modeler = new BpmnModeler({
                            container: bpmnContainerRef.current,
                            keyboard: { bindTo: document }
                        });

                        try {
                            await modeler.importXML(xml);
                            const canvas = modeler.get('canvas');
                            setTimeout(() => {
                                canvas.zoom('fit-viewport', 'auto');
                            }, 100);
                        } catch (err) {
                            console.error('Error rendering BPMN:', err);
                        }
                    }
                }
            }
        };

        generateAndRenderBpmn();

        // Cleanup function
        return () => {
            if (modeler) {
                modeler.destroy();
            }
        };
    }, [tobeProposals, segmentedData, tobeBpmnXml]);

    if (!processData && !validatedData) {
        return <EmptyState />;
    }

    if (!classifiedData && !segmentedData) {
        return (
            <EmptyState
                title="Datos Insuficientes"
                description="Para generar el proceso TO-BE, primero debes completar la Clasificación Lean (A. Desperdicios) y el Segmentador de Actividades (A. Actividades)."
                actionLabel="Ir a Clasificación"
                actionPath="#classifier"
            />
        );
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex justify-between items-center">
                <motion.div
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                >
                    <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
                        🎯 Proceso TO-BE
                    </h1>
                    <p className="text-gray-600 dark:text-gray-400">
                        Generación de propuestas de mejora y optimización
                    </p>
                </motion.div>

                {tobeProposals && (
                    <motion.div
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                    >
                        <Button
                            icon={RotateCcw}
                            onClick={handleGenerateTOBE}
                            loading={loading.tobe}
                            variant="outline"
                        >
                            Regenerar Proceso TO-BE
                        </Button>
                    </motion.div>
                )}
            </div>

            {/* Generate TO-BE */}
            {!tobeProposals && (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                >
                    <Card>
                        <CardHeader>
                            <CardTitle>Generar Proceso TO-BE</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="text-center py-8">
                                <TrendingUp className="w-16 h-16 mx-auto mb-4 text-primary-600" />
                                <p className="text-gray-600 dark:text-gray-400 mb-6">
                                    Genera propuestas de mejora basadas en la clasificación Lean y análisis del proceso
                                </p>

                                {!processContext ? (
                                    <div className="mb-6 p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg text-sm text-yellow-800 dark:text-yellow-200">
                                        ⚠️ Debes configurar el <strong>Contexto del Proceso</strong> en el menú de configuración (⚙️) antes de continuar.
                                    </div>
                                ) : (
                                    <div className="mb-6 p-4 bg-green-50 dark:bg-green-900/20 rounded-lg text-sm text-green-800 dark:text-green-200">
                                        ✅ Contexto configurado: <span className="italic">"{(processContext || '').slice(0, 50)}..."</span>
                                    </div>
                                )}

                                <Button
                                    icon={Play}
                                    onClick={handleGenerateTOBE}
                                    loading={loading.tobe}
                                    size="lg"
                                    disabled={!processContext}
                                >
                                    Generar Propuestas TO-BE con IA
                                </Button>
                            </div>

                            {loading.tobe && progress > 0 && (
                                <div className="mt-6">
                                    <ProgressBar
                                        value={progress}
                                        max={100}
                                        label="Generando propuestas de mejora..."
                                        showPercentage
                                    />
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </motion.div>
            )}

            {/* Comparison Metrics */}
            {tobeComparison && (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                >
                    <Card>
                        <CardHeader>
                            <div className="flex items-center gap-2">
                                <GitCompare className="w-5 h-5 text-primary-600" />
                                <CardTitle>Comparación AS-IS vs TO-BE</CardTitle>
                            </div>
                        </CardHeader>
                        <CardContent>
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                                {/* KPI 1: Reducción de Tiempo Total */}
                                <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
                                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Reducción Tiempo Total</p>
                                    <p className="text-2xl font-bold text-blue-600">
                                        {formatTime(tobeComparison.improvements?.time_reduction || 0)}
                                    </p>
                                    <p className="text-xs text-gray-500 mt-1">
                                        {formatPercentage(tobeComparison.improvements?.time_reduction_pct || 0)} menos
                                    </p>
                                </div>

                                {/* KPI 2: Reducción de Personal */}
                                <div className="bg-purple-50 dark:bg-purple-900/20 p-4 rounded-lg">
                                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Reducción de Personal</p>
                                    <p className="text-2xl font-bold text-purple-600">
                                        {(() => {
                                            const reduction = tobeProposals.reduce((acc, curr) => {
                                                const original = Number(curr.personas_originales) || 0;
                                                const improved = Number(curr.personas_mejoradas) || 0;
                                                return acc + (original - improved);
                                            }, 0);
                                            return formatNumber(reduction);
                                        })()}
                                    </p>
                                    <p className="text-xs text-gray-500 mt-1">Personas liberadas</p>
                                </div>

                                {/* KPI 3: Actividades Optimizadas/Eliminadas */}
                                <div className="bg-green-50 dark:bg-green-900/20 p-4 rounded-lg">
                                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Activ. Optimizadas/Elim.</p>
                                    <p className="text-2xl font-bold text-green-600">
                                        {formatNumber(
                                            tobeProposals.filter(p =>
                                                ['Optimizada', 'Eliminada', 'Automatizada', 'Combinada'].includes(p.accion)
                                            ).length
                                        )}
                                    </p>
                                    <p className="text-xs text-gray-500 mt-1">
                                        De {formatNumber(tobeProposals.length)} totales
                                    </p>
                                </div>

                                {/* KPI 4: Reducción Tiempo Promedio */}
                                <div className="bg-orange-50 dark:bg-orange-900/20 p-4 rounded-lg">
                                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Reducción Promedio/Act.</p>
                                    <p className="text-2xl font-bold text-orange-600">
                                        {(() => {
                                            const totalReduction = tobeComparison.improvements?.time_reduction || 0;
                                            const count = tobeProposals.length || 1;
                                            return formatTime(totalReduction / count);
                                        })()}
                                    </p>
                                    <p className="text-xs text-gray-500 mt-1">Por actividad</p>
                                </div>
                            </div>

                            {/* Impacto General - Resumen de Mejoras */}
                            <div className="mb-6 bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-800/50 p-6 rounded-xl border border-gray-200 dark:border-gray-700">
                                <h4 className="flex items-center gap-2 font-bold text-lg text-gray-900 dark:text-white mb-3">
                                    <TrendingUp className="w-5 h-5 text-green-600" />
                                    Impacto General del Nuevo Proceso
                                </h4>
                                <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                                    La implementación del proceso TO-BE generará una reducción del <span className="font-bold text-green-600">{formatPercentage(tobeComparison.improvements?.time_reduction_pct || 0)}</span> en el tiempo total de ejecución,
                                    liberando aproximadamente <span className="font-bold text-purple-600">{(() => {
                                        return formatNumber(tobeProposals.reduce((acc, curr) => acc + ((Number(curr.personas_originales) || 0) - (Number(curr.personas_mejoradas) || 0)), 0));
                                    })()} recursos</span>.
                                    Se han intervenido <span className="font-bold text-blue-600">{tobeProposals.filter(p => ['Optimizada', 'Eliminada', 'Automatizada', 'Combinada'].includes(p.accion)).length} actividades</span> clave
                                    mediante estrategias de eliminación, automatización y optimización, logrando un proceso más ágil y eficiente.
                                </p>
                            </div>

                            {/* AS-IS vs TO-BE Comparison */}
                            <div className="mt-6 grid md:grid-cols-2 gap-6">
                                <div>
                                    <h4 className="font-semibold text-gray-900 dark:text-white mb-3">
                                        Proceso AS-IS (Actual)
                                    </h4>
                                    <div className="space-y-2 text-sm">
                                        <div className="flex justify-between">
                                            <span className="text-gray-600 dark:text-gray-400">Total Actividades:</span>
                                            <span className="font-medium text-gray-900 dark:text-white">{formatNumber(tobeComparison.comparison?.asis?.total_activities || 0)}</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-gray-600 dark:text-gray-400">Tiempo Total:</span>
                                            <span className="font-medium text-gray-900 dark:text-white">{formatTime(tobeComparison.comparison?.asis?.total_time || 0)}</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-gray-600 dark:text-gray-400">Automatizadas:</span>
                                            <span className="font-medium text-gray-900 dark:text-white">{formatNumber(tobeComparison.comparison?.asis?.automated_activities || 0)}</span>
                                        </div>
                                    </div>
                                </div>

                                <div>
                                    <h4 className="font-semibold text-gray-900 dark:text-white mb-3">
                                        Proceso TO-BE (Propuesto)
                                    </h4>
                                    <div className="space-y-2 text-sm">
                                        <div className="flex justify-between">
                                            <span className="text-gray-600 dark:text-gray-400">Total Actividades:</span>
                                            <span className="font-medium text-green-600">{formatNumber(tobeComparison.comparison?.tobe?.total_activities || 0)}</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-gray-600 dark:text-gray-400">Tiempo Total:</span>
                                            <span className="font-medium text-green-600">{formatTime(tobeComparison.comparison?.tobe?.total_time || 0)}</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-gray-600 dark:text-gray-400">Automatizadas:</span>
                                            <span className="font-medium text-green-600">{formatNumber(tobeComparison.comparison?.tobe?.automated_activities || 0)}</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </motion.div>
            )}

            {/* SIPOC Diagram */}
            {sipocData && (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                >
                    <Card>
                        <CardHeader>
                            <CardTitle>Diagrama SIPOC (TO-BE)</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
                                <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
                                    <h4 className="font-bold text-center mb-2 text-primary-600">Suppliers</h4>
                                    <ul className="text-sm space-y-1 list-disc pl-4 text-gray-700 dark:text-gray-300">
                                        {sipocData.suppliers?.map((item, i) => <li key={i}>{item}</li>)}
                                    </ul>
                                </div>
                                <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
                                    <h4 className="font-bold text-center mb-2 text-primary-600">Inputs</h4>
                                    <ul className="text-sm space-y-1 list-disc pl-4 text-gray-700 dark:text-gray-300">
                                        {sipocData.inputs?.map((item, i) => <li key={i}>{item}</li>)}
                                    </ul>
                                </div>
                                <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
                                    <h4 className="font-bold text-center mb-2 text-primary-600">Process</h4>
                                    <ul className="text-sm space-y-1 list-decimal pl-4 text-gray-700 dark:text-gray-300">
                                        {sipocData.process?.map((item, i) => <li key={i}>{item.nombre}</li>)}
                                    </ul>
                                </div>
                                <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
                                    <h4 className="font-bold text-center mb-2 text-primary-600">Outputs</h4>
                                    <ul className="text-sm space-y-1 list-disc pl-4 text-gray-700 dark:text-gray-300">
                                        {sipocData.outputs?.map((item, i) => <li key={i}>{item}</li>)}
                                    </ul>
                                </div>
                                <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
                                    <h4 className="font-bold text-center mb-2 text-primary-600">Customers</h4>
                                    <ul className="text-sm space-y-1 list-disc pl-4 text-gray-700 dark:text-gray-300">
                                        {sipocData.customers?.map((item, i) => <li key={i}>{item}</li>)}
                                    </ul>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </motion.div>
            )}

            {/* Summary Table */}
            {tobeProposals && tobeProposals.length > 0 && segmentedData && (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                >
                    <Card>
                        <CardHeader>
                            <div className="flex justify-between items-center">
                                <CardTitle>Resumen Detallado TO-BE</CardTitle>
                                <Button
                                    icon={Download}
                                    onClick={handleExport}
                                    variant="outline"
                                    size="sm"
                                >
                                    Exportar Excel
                                </Button>
                            </div>
                        </CardHeader>
                        <CardContent>
                            <div className="overflow-x-auto max-h-[600px] overflow-y-auto">
                                <table className="w-full text-sm">
                                    <thead className="bg-gray-50 dark:bg-gray-800 sticky top-0 z-10">
                                        <tr>
                                            <th className="px-3 py-2 text-left font-semibold text-xs text-gray-700 dark:text-gray-300">#</th>
                                            <th className="px-3 py-2 text-left font-semibold text-xs text-gray-700 dark:text-gray-300">Actividad</th>
                                            <th className="px-3 py-2 text-left font-semibold text-xs text-gray-700 dark:text-gray-300">Responsable</th>
                                            <th className="px-3 py-2 text-left font-semibold text-xs text-gray-700 dark:text-gray-300">Tipo Actividad</th>
                                            <th className="px-3 py-2 text-left font-semibold text-xs text-gray-700 dark:text-gray-300">Clasificación Lean</th>
                                            <th className="px-3 py-2 text-left font-semibold text-xs text-gray-700 dark:text-gray-300">Tipo Desperdicio</th>
                                            <th className="px-3 py-2 text-left font-semibold text-xs text-gray-700 dark:text-gray-300">Tiempo Estándar</th>
                                            <th className="px-3 py-2 text-left font-semibold text-xs text-gray-700 dark:text-gray-300">Acción TO-BE</th>
                                            <th className="px-3 py-2 text-left font-semibold text-xs text-gray-700 dark:text-gray-300">Tiempo Mejorado</th>
                                            <th className="px-3 py-2 text-left font-semibold text-xs text-gray-700 dark:text-gray-300">Reducción</th>
                                            <th className="px-3 py-2 text-left font-semibold text-xs text-gray-700 dark:text-gray-300">Justificación Mejora</th>
                                        </tr>
                                    </thead>
                                    <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-800">
                                        {segmentedData.map((item, index) => {
                                            const proposal = tobeProposals.find(p => p.id === item.id) || tobeProposals[index] || {};
                                            const clasificacion = item['Clasificación Lean'] || item.clasificacion || 'N/A';

                                            let clasificacionColor = 'bg-gray-500';
                                            if (clasificacion === 'Valor' || clasificacion === 'VA') clasificacionColor = 'bg-green-600';
                                            else if (clasificacion === 'Falta detalle' || clasificacion === 'NVA-N') clasificacionColor = 'bg-yellow-600';
                                            else if (clasificacion === 'Desperdicio' || clasificacion === 'NVA') clasificacionColor = 'bg-red-600';

                                            return (
                                                <tr key={index} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                                                    <td className="px-3 py-2 text-gray-500 dark:text-gray-400">{index + 1}</td>
                                                    <td className="px-3 py-2 font-medium text-gray-900 dark:text-white">{item.Actividad || item.nombre}</td>
                                                    <td className="px-3 py-2 text-gray-600 dark:text-gray-400">{item['Cargo que ejecuta la tarea'] || item.responsable}</td>
                                                    <td className="px-3 py-2 text-gray-600 dark:text-gray-400">{item.tipo_actividad || item.tipo || 'N/A'}</td>
                                                    <td className="px-3 py-2">
                                                        <span className={`px-2 py-1 rounded-full text-xs font-medium text-white ${clasificacionColor}`}>
                                                            {clasificacion}
                                                        </span>
                                                    </td>
                                                    <td className="px-3 py-2 text-gray-600 dark:text-gray-400">{item['Tipo Desperdicio'] || item.tipo_desperdicio || '-'}</td>
                                                    <td className="px-3 py-2 text-gray-600 dark:text-gray-400">{item['Tiempo Estándar'] || item.tiempo} min</td>
                                                    <td className="px-3 py-2">
                                                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${proposal.accion === 'Eliminada' ? 'bg-red-100 text-red-800' :
                                                            proposal.accion === 'Automatizada' ? 'bg-blue-100 text-blue-800' :
                                                                proposal.accion === 'Optimizada' ? 'bg-green-100 text-green-800' :
                                                                    'bg-gray-100 text-gray-800'
                                                            }`}>
                                                            {proposal.accion || 'Mantenida'}
                                                        </span>
                                                    </td>
                                                    <td className="px-3 py-2 text-gray-600 dark:text-gray-400 font-medium text-green-600">
                                                        {proposal.tiempo_mejorado_minutos !== undefined ? `${proposal.tiempo_mejorado_minutos} min` : '-'}
                                                    </td>
                                                    <td className="px-3 py-2 text-blue-600 font-medium">
                                                        {proposal.reduccion_tiempo_porcentaje ? `${proposal.reduccion_tiempo_porcentaje}%` : '-'}
                                                    </td>
                                                    <td className="px-3 py-2 text-xs text-gray-500 italic max-w-xs truncate" title={proposal.justificacion}>
                                                        {proposal.justificacion || '-'}
                                                    </td>
                                                </tr>
                                            );
                                        })}
                                    </tbody>
                                </table>
                            </div>
                        </CardContent>
                    </Card>
                </motion.div>
            )}

            {/* TO-BE Process Flowchart */}
            {tobeBpmnXml && (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                >
                    <Card>
                        <CardHeader>
                            <CardTitle>Diagrama de Flujo TO-BE (Proceso Optimizado)</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div
                                ref={bpmnContainerRef}
                                className="w-full h-[600px] border border-gray-200 dark:border-gray-700 rounded-lg"
                                style={{ backgroundColor: '#fafafa' }}
                            />
                        </CardContent>
                    </Card>
                </motion.div>
            )}

            {/* Improvement Proposals */}
            {tobeProposals && (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                >
                    <Card>
                        <CardHeader>
                            <div className="flex items-center gap-2">
                                <Lightbulb className="w-5 h-5 text-yellow-500" />
                                <CardTitle>Propuestas de Mejora</CardTitle>
                            </div>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-4">
                                {Array.isArray(tobeProposals) ? (
                                    tobeProposals.map((proposal, index) => (
                                        <div
                                            key={index}
                                            className="border-l-4 border-primary-500 pl-4 py-3 bg-gray-50 dark:bg-gray-800 rounded-r-lg"
                                        >
                                            <div className="flex items-center justify-between mb-2">
                                                <h4 className="font-semibold text-gray-900 dark:text-white">
                                                    Actividad {index + 1}: {proposal.nombre || `Mejora ${index + 1}`}
                                                </h4>
                                                {proposal.accion && (
                                                    <span className={`text-xs px-2 py-1 rounded-full font-medium ${proposal.accion === 'Eliminada' ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' :
                                                        proposal.accion === 'Automatizada' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' :
                                                            proposal.accion === 'Optimizada' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' :
                                                                proposal.accion === 'Combinada' ? 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400' :
                                                                    'bg-gray-100 text-gray-700 dark:bg-gray-900/30 dark:text-gray-400'
                                                        }`}>
                                                        {proposal.accion}
                                                    </span>
                                                )}
                                            </div>
                                            <p className="text-sm text-gray-700 dark:text-gray-300 mb-2">
                                                {proposal.descripcion || 'Sin descripción'}
                                            </p>
                                            {proposal.justificacion && (
                                                <p className="text-xs text-gray-600 dark:text-gray-400 mb-2 italic">
                                                    💡 {proposal.justificacion}
                                                </p>
                                            )}
                                            {(proposal.tiempo_original_minutos !== undefined || proposal.tiempo_mejorado_minutos !== undefined) && (
                                                <div className="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400 mt-2 pt-2 border-t border-gray-200 dark:border-gray-700">
                                                    {proposal.tiempo_original_minutos !== undefined && (
                                                        <span>⏱️ Tiempo original: {proposal.tiempo_original_minutos} min</span>
                                                    )}
                                                    {proposal.tiempo_mejorado_minutos !== undefined && (
                                                        <span className="text-green-600 dark:text-green-400 font-medium">
                                                            ⏱️ Tiempo mejorado: {proposal.tiempo_mejorado_minutos} min
                                                        </span>
                                                    )}
                                                    {proposal.reduccion_tiempo_porcentaje !== undefined && (
                                                        <span className="text-blue-600 dark:text-blue-400 font-medium">
                                                            📉 Reducción: {proposal.reduccion_tiempo_porcentaje}%
                                                        </span>
                                                    )}
                                                </div>
                                            )}
                                        </div>
                                    ))
                                ) : (
                                    <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                                        <p>Las propuestas de mejora se generarán con IA</p>
                                    </div>
                                )}
                            </div>
                        </CardContent>
                    </Card>
                </motion.div>
            )}
        </div>
    );
}
