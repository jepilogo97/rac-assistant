/**
 * Classifier Page - Lean Classification of Activities
 */
import { useState } from 'react';
import { motion } from 'framer-motion';
import { Play, Download, RefreshCw } from 'lucide-react';
import toast from 'react-hot-toast';
import useStore from '../store';
import endpoints from '../services/endpoints';
import Card, { CardHeader, CardTitle, CardContent } from '../components/common/Card';
import Button from '../components/common/Button';
import ProgressBar from '../components/common/ProgressBar';
import { formatNumber, formatPercentage } from '../utils/formatters';
import EmptyState from '../components/common/EmptyState';
import { WASTE_CATEGORIES } from '../utils/constants';

export default function ClassifierPage() {
    const {
        processData,
        validatedData,
        classifiedData,
        classificationSummary,
        apiKey,
        setClassifiedData,
        setClassificationSummary,
        loading,
        setLoading,
    } = useStore();

    const [progress, setProgress] = useState(0);

    const handleClassify = async () => {
        if (!apiKey) {
            toast.error('Por favor configura tu API Key de Google Gemini en la configuración');
            return;
        }

        const dataToClassify = validatedData || processData;
        if (!dataToClassify) {
            toast.error('No hay datos disponibles para clasificar');
            return;
        }

        setLoading('classification', true);
        setProgress(10);

        try {
            // Simulate progress while waiting for AI
            const interval = setInterval(() => {
                setProgress((prev) => {
                    if (prev >= 90) return prev;
                    return prev + 5;
                });
            }, 1000);

            const response = await endpoints.classification.classify(dataToClassify, apiKey);

            clearInterval(interval);
            setProgress(100);

            if (response.classified_data) {
                // Merge original data (especially time) with classification results
                const mergedData = response.classified_data.map((item, index) => {
                    // Use index to find original item since backend preserves order
                    const originalItem = dataToClassify[index] || {};

                    // Extract time from various possible keys in both source and result
                    const timeValue =
                        item['Tiempo Estándar'] ||
                        item.time ||
                        item.tiempo ||
                        originalItem['Tiempo Estándar'] ||
                        originalItem['Tiempo Estándar (Min/Tarea)'] ||
                        originalItem['Tiempo Promedio'] ||
                        originalItem['Tiempo Prom (Min/Tarea)'] ||
                        originalItem.time ||
                        originalItem.tiempo ||
                        '-';

                    return {
                        ...item,
                        'Tiempo Estándar': timeValue
                    };
                });
                setClassifiedData(mergedData);
            }

            if (response.summary) {
                setClassificationSummary(response.summary);
            }

            toast.success('Clasificación completada exitosamente');
        } catch (error) {
            console.error('Error en clasificación:', error);
            toast.error(error.message || 'Error al realizar la clasificación');
            setProgress(0);
        } finally {
            setLoading('classification', false);
        }
    };

    const handleExport = async () => {
        try {
            const blob = await endpoints.classification.export(classifiedData);
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `clasificacion_lean_${new Date().toISOString().split('T')[0]}.xlsx`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            toast.success('Clasificación exportada');
        } catch (error) {
            toast.error(error.message || 'Error al exportar clasificación');
        }
    };

    // ... (inside component)

    // ... (inside component)

    if (!processData && !validatedData) {
        return <EmptyState />;
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex items-center justify-between"
            >
                <div>
                    <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
                        🏷️ Clasificador Lean
                    </h1>
                    <p className="text-gray-600 dark:text-gray-400">
                        Clasificación de desperdicios según metodología Lean
                    </p>
                </div>

                <div className="flex items-center gap-2">
                    <Button
                        variant="secondary"
                        size="sm"
                        icon={RefreshCw}
                        onClick={handleClassify}
                        disabled={loading.classification}
                    >
                        Reclasificar
                    </Button>
                    <Button
                        variant="primary"
                        size="sm"
                        icon={Download}
                        onClick={handleExport}
                        disabled={!classifiedData}
                    >
                        Exportar Excel
                    </Button>
                </div>
            </motion.div>

            {/* Classification Action */}
            {!classifiedData && (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                >
                    <Card>
                        <CardHeader>
                            <CardTitle>Iniciar Clasificación</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="text-center py-8">
                                <p className="text-gray-600 dark:text-gray-400 mb-6">
                                    Clasifica las actividades del proceso según los 8 desperdicios de Lean Manufacturing
                                </p>
                                <Button
                                    icon={Play}
                                    onClick={handleClassify}
                                    loading={loading.classification}
                                    size="lg"
                                >
                                    Iniciar Clasificación con IA
                                </Button>
                            </div>

                            {loading.classification && progress > 0 && (
                                <div className="mt-6">
                                    <ProgressBar
                                        value={progress}
                                        max={100}
                                        label="Clasificando actividades..."
                                        showPercentage
                                    />
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </motion.div>
            )}

            {/* Classification Summary */}
            {classificationSummary && (
                <>
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                    >
                        <Card>
                            <CardHeader>
                                <CardTitle>📊 Resumen de Clasificación Lean</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                    {/* VA - Valor Agregado */}
                                    <div className="bg-green-50 dark:bg-green-900/20 p-6 rounded-lg border-2 border-green-200 dark:border-green-800">
                                        <div className="flex items-center justify-between mb-3">
                                            <h3 className="text-lg font-bold text-green-700 dark:text-green-400">
                                                ✅ Valor Agregado (VA)
                                            </h3>
                                        </div>
                                        <p className="text-4xl font-bold text-green-600 mb-2">
                                            {formatNumber(classificationSummary.value_added_activities || 0)}
                                        </p>
                                        <p className="text-sm text-green-600 dark:text-green-400">
                                            {formatPercentage((classificationSummary.value_added_activities || 0) / (classificationSummary.total_activities || 1) * 100)}
                                        </p>
                                        <p className="text-xs text-gray-600 dark:text-gray-400 mt-2">
                                            Actividades que agregan valor al cliente
                                        </p>
                                    </div>

                                    {/* NVA-N - Necesario pero sin Valor */}
                                    <div className="bg-yellow-50 dark:bg-yellow-900/20 p-6 rounded-lg border-2 border-yellow-200 dark:border-yellow-800">
                                        <div className="flex items-center justify-between mb-3">
                                            <h3 className="text-lg font-bold text-yellow-700 dark:text-yellow-400">
                                                ⚠️ Necesario sin Valor (NVA-N)
                                            </h3>
                                        </div>
                                        <p className="text-4xl font-bold text-yellow-600 mb-2">
                                            {formatNumber(classificationSummary.necessary_non_value || 0)}
                                        </p>
                                        <p className="text-sm text-yellow-600 dark:text-yellow-400">
                                            {formatPercentage((classificationSummary.necessary_non_value || 0) / (classificationSummary.total_activities || 1) * 100)}
                                        </p>
                                        <p className="text-xs text-gray-600 dark:text-gray-400 mt-2">
                                            Actividades necesarias pero que no agregan valor
                                        </p>
                                    </div>

                                    {/* NVA - Desperdicio */}
                                    <div className="bg-red-50 dark:bg-red-900/20 p-6 rounded-lg border-2 border-red-200 dark:border-red-800">
                                        <div className="flex items-center justify-between mb-3">
                                            <h3 className="text-lg font-bold text-red-700 dark:text-red-400">
                                                ❌ Desperdicio (NVA)
                                            </h3>
                                        </div>
                                        <p className="text-4xl font-bold text-red-600 mb-2">
                                            {formatNumber(classificationSummary.waste_activities || 0)}
                                        </p>
                                        <p className="text-sm text-red-600 dark:text-red-400">
                                            {formatPercentage(classificationSummary.waste_percentage || 0)}
                                        </p>
                                        <p className="text-xs text-gray-600 dark:text-gray-400 mt-2">
                                            Actividades que deben eliminarse o minimizarse
                                        </p>
                                    </div>
                                </div>

                                {/* Total Summary Bar */}
                                <div className="mt-6 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                                    <div className="flex items-center justify-between mb-2">
                                        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                                            Total de Actividades Analizadas
                                        </span>
                                        <span className="text-lg font-bold text-primary-600">
                                            {formatNumber(classificationSummary.total_activities || 0)}
                                        </span>
                                    </div>
                                    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-4 flex overflow-hidden">
                                        <div
                                            className="bg-green-500 flex items-center justify-center text-xs text-white font-medium"
                                            style={{
                                                width: `${((classificationSummary.value_added_activities || 0) / (classificationSummary.total_activities || 1) * 100)}%`
                                            }}
                                            title={`VA: ${formatPercentage((classificationSummary.value_added_activities || 0) / (classificationSummary.total_activities || 1) * 100)}`}
                                        >
                                            {((classificationSummary.value_added_activities || 0) / (classificationSummary.total_activities || 1) * 100) > 10 && 'VA'}
                                        </div>
                                        <div
                                            className="bg-yellow-500 flex items-center justify-center text-xs text-white font-medium"
                                            style={{
                                                width: `${((classificationSummary.necessary_non_value || 0) / (classificationSummary.total_activities || 1) * 100)}%`
                                            }}
                                            title={`NVA-N: ${formatPercentage((classificationSummary.necessary_non_value || 0) / (classificationSummary.total_activities || 1) * 100)}`}
                                        >
                                            {((classificationSummary.necessary_non_value || 0) / (classificationSummary.total_activities || 1) * 100) > 10 && 'NVA-N'}
                                        </div>
                                        <div
                                            className="bg-red-500 flex items-center justify-center text-xs text-white font-medium"
                                            style={{
                                                width: `${((classificationSummary.waste_activities || 0) / (classificationSummary.total_activities || 1) * 100)}%`
                                            }}
                                            title={`NVA: ${formatPercentage(classificationSummary.waste_percentage || 0)}`}
                                        >
                                            {classificationSummary.waste_percentage > 10 && 'NVA'}
                                        </div>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    </motion.div>
                </>
            )}

            {/* Waste Distribution */}
            {classificationSummary && classificationSummary.waste_distribution && (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                >
                    <Card>
                        <CardHeader>
                            <CardTitle>Distribución de Desperdicios</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-3">
                                {Object.entries(classificationSummary.waste_distribution).map(([waste, count]) => {
                                    const category = WASTE_CATEGORIES.find(c => c.id === waste);
                                    const percentage = (count / (classificationSummary.total_activities || 1)) * 100;

                                    return (
                                        <div key={waste} className="flex items-center gap-4">
                                            <div className="flex-1">
                                                <div className="flex items-center justify-between mb-1">
                                                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                                                        {category?.name || waste}
                                                    </span>
                                                    <span className="text-sm text-gray-600 dark:text-gray-400">
                                                        {count} ({formatPercentage(percentage, 1)})
                                                    </span>
                                                </div>
                                                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                                                    <div
                                                        className="h-2 rounded-full transition-all duration-500"
                                                        style={{
                                                            width: `${percentage}%`,
                                                            backgroundColor: category?.color || '#3b82f6'
                                                        }}
                                                    />
                                                </div>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        </CardContent>
                    </Card>
                </motion.div>
            )}

            {/* Classification Results Table */}
            {classifiedData && (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                >
                    <Card>
                        <CardHeader>
                            <CardTitle>📋 Resultados Detallados de Clasificación</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="overflow-x-auto max-h-[600px] overflow-y-auto">
                                <table className="w-full text-sm">
                                    <thead className="bg-gray-50 dark:bg-gray-800 sticky top-0 z-10">
                                        <tr>
                                            <th className="px-3 py-2 text-left font-semibold text-xs text-gray-700 dark:text-gray-300">#</th>
                                            <th className="px-3 py-2 text-left font-semibold text-xs text-gray-700 dark:text-gray-300">Actividad</th>
                                            <th className="px-3 py-2 text-left font-semibold text-xs text-gray-700 dark:text-gray-300">Descripción</th>
                                            <th className="px-3 py-2 text-left font-semibold text-xs text-gray-700 dark:text-gray-300">Responsable</th>
                                            <th className="px-3 py-2 text-left font-semibold text-xs text-gray-700 dark:text-gray-300 min-w-[180px]">Clasificación Lean</th>
                                            <th className="px-3 py-2 text-left font-semibold text-xs text-gray-700 dark:text-gray-300">Tipo Desperdicio</th>
                                            <th className="px-3 py-2 text-left font-semibold text-xs text-gray-700 dark:text-gray-300">Justificación</th>
                                            <th className="px-3 py-2 text-left font-semibold text-xs text-gray-700 dark:text-gray-300">Tiempo (min)</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {classifiedData.map((row, index) => {
                                            // Map field names (backend uses different names)
                                            const clasificacion = row['Clasificación Lean'] || row.clasificacion || 'N/A';
                                            const tipoDesperdicio = row['Tipo Desperdicio'] || row.tipo_desperdicio || row.desperdicio || '';
                                            const justificacion = row['Justificación'] || row.justificacion || 'N/A';

                                            const wasteCategory = WASTE_CATEGORIES.find(c => c.id === tipoDesperdicio);

                                            // Determine classification color
                                            let clasificacionColor = 'bg-gray-500';
                                            let clasificacionText = clasificacion;

                                            if (clasificacion === 'Valor' || clasificacion === 'VA') {
                                                clasificacionColor = 'bg-green-600';
                                                clasificacionText = 'VA - Valor';
                                            } else if (clasificacion === 'Falta detalle' || clasificacion === 'NVA-N') {
                                                clasificacionColor = 'bg-yellow-600';
                                                clasificacionText = 'NVA-N - Necesario';
                                            } else if (clasificacion === 'Desperdicio' || clasificacion === 'NVA') {
                                                clasificacionColor = 'bg-red-600';
                                                clasificacionText = 'NVA - Desperdicio';
                                            }

                                            return (
                                                <tr key={index} className="border-t border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800">
                                                    <td className="px-3 py-2 text-gray-500 dark:text-gray-400">
                                                        {index + 1}
                                                    </td>
                                                    <td className="px-3 py-2 font-medium text-gray-900 dark:text-white">
                                                        {row.Actividad || row.actividad || row.name || 'N/A'}
                                                    </td>
                                                    <td className="px-3 py-2 text-gray-600 dark:text-gray-400 max-w-md">
                                                        <div className="whitespace-normal break-words">
                                                            {row.Descripción || row.descripcion || row.description || 'N/A'}
                                                        </div>
                                                    </td>
                                                    <td className="px-3 py-2 text-gray-600 dark:text-gray-400">
                                                        {row['Cargo que ejecuta la tarea'] || row.responsible || row.responsable || 'N/A'}
                                                    </td>
                                                    <td className="px-3 py-2 min-w-[180px]">
                                                        <span
                                                            className={`px-2 py-1 rounded-full text-xs font-medium text-white ${clasificacionColor}`}
                                                        >
                                                            {clasificacionText}
                                                        </span>
                                                    </td>
                                                    <td className="px-3 py-2">
                                                        {tipoDesperdicio ? (
                                                            <span
                                                                className="px-2 py-1 rounded-full text-xs font-medium text-white"
                                                                style={{ backgroundColor: wasteCategory?.color || '#6b7280' }}
                                                            >
                                                                {wasteCategory?.name || tipoDesperdicio}
                                                            </span>
                                                        ) : (
                                                            <span className="text-gray-400 text-xs">-</span>
                                                        )}
                                                    </td>
                                                    <td className="px-3 py-2 text-gray-600 dark:text-gray-400 max-w-lg">
                                                        <div className="whitespace-normal break-words">
                                                            {justificacion}
                                                        </div>
                                                    </td>
                                                    <td className="px-3 py-2 text-gray-600 dark:text-gray-400 text-right">
                                                        {row['Tiempo Estándar'] || row.time || row.tiempo || '-'}
                                                    </td>
                                                </tr>
                                            );
                                        })}
                                    </tbody>
                                </table>
                                {classifiedData.length > 50 && (
                                    <p className="text-sm text-gray-500 dark:text-gray-400 mt-4 text-center">
                                        Mostrando todas las {formatNumber(classifiedData.length)} actividades clasificadas
                                    </p>
                                )}
                            </div>
                        </CardContent>
                    </Card>
                </motion.div>
            )}
        </div>
    );
}
