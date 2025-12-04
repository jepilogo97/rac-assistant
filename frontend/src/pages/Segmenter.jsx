/**
 * Segmenter Page - Activity Segmentation
 */
import { useState } from 'react';
import { motion } from 'framer-motion';
import { Play, Layers, RotateCcw, Download } from 'lucide-react';
import toast from 'react-hot-toast';
import useStore from '../store';
import endpoints from '../services/endpoints';
import Card, { CardHeader, CardTitle, CardContent } from '../components/common/Card';
import Button from '../components/common/Button';
import ProgressBar from '../components/common/ProgressBar';
import { formatNumber } from '../utils/formatters';
import EmptyState from '../components/common/EmptyState';

export default function SegmenterPage() {
    const {
        processData,
        validatedData,
        classifiedData,
        segmentedData,
        segments,
        apiKey,
        setSegmentedData,
        setSegments,
        loading,
        setLoading,
    } = useStore();

    const [progress, setProgress] = useState(0);

    const handleSegment = async () => {
        // Validate that Lean Classification has been run first
        if (!classifiedData || classifiedData.length === 0) {
            toast.error('Primero debes ejecutar el Clasificador Lean (A. Desperdicios) antes de segmentar actividades');
            return;
        }

        const data = classifiedData;

        if (!apiKey) {
            toast.error('Por favor configura tu API Key de Google Gemini');
            return;
        }

        setLoading('segmentation', true);
        setProgress(0);

        try {
            // Simulate progress
            const progressInterval = setInterval(() => {
                setProgress(prev => Math.min(prev + 15, 90));
            }, 600);

            const result = await endpoints.segmentation.segment(data, apiKey);

            clearInterval(progressInterval);
            setProgress(100);

            if (result.success) {
                setSegmentedData(result.segmented_data);
                setSegments(result.segments);
                toast.success('Segmentación completada exitosamente');
            }
        } catch (error) {
            toast.error(error.message || 'Error al segmentar actividades');
        } finally {
            setLoading('segmentation', false);
            setTimeout(() => setProgress(0), 1000);
        }
    };

    const handleExport = async () => {
        if (!segmentedData || segmentedData.length === 0) {
            toast.error('No hay datos para exportar');
            return;
        }

        try {
            const blob = await endpoints.segmentation.export(segmentedData);
            const url = window.URL.createObjectURL(new Blob([blob]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', 'segmentacion_actividades.xlsx');
            document.body.appendChild(link);
            link.click();
            link.parentNode.removeChild(link);
            toast.success('Archivo exportado exitosamente');
        } catch (error) {
            console.error('Export error:', error);
            toast.error('Error al exportar el archivo');
        }
    };

    const getSegmentColor = (index) => {
        const colors = [
            '#3b82f6', '#10b981', '#f59e0b', '#ef4444',
            '#8b5cf6', '#ec4899', '#14b8a6', '#f97316'
        ];
        return colors[index % colors.length];
    };

    if (!processData && !validatedData) {
        return <EmptyState />;
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
                        📊 Segmentador de Actividades
                    </h1>
                    <p className="text-gray-600 dark:text-gray-400">
                        Segmentación inteligente del proceso en grupos lógicos
                    </p>
                </motion.div>

                {segmentedData && (
                    <motion.div
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                    >
                        <Button
                            icon={RotateCcw}
                            onClick={handleSegment}
                            loading={loading.segmentation}
                            variant="outline"
                        >
                            Regenerar Segmentación
                        </Button>
                    </motion.div>
                )}
            </div>

            {/* Segmentation Action */}
            {!segmentedData && (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                >
                    <Card>
                        <CardHeader>
                            <CardTitle>Iniciar Segmentación</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="text-center py-8">
                                <Layers className="w-16 h-16 mx-auto mb-4 text-primary-600" />
                                <p className="text-gray-600 dark:text-gray-400 mb-6">
                                    Agrupa las actividades del proceso en segmentos lógicos usando IA
                                </p>
                                <Button
                                    icon={Play}
                                    onClick={handleSegment}
                                    loading={loading.segmentation}
                                    size="lg"
                                >
                                    Iniciar Segmentación con IA
                                </Button>
                            </div>

                            {loading.segmentation && progress > 0 && (
                                <div className="mt-6">
                                    <ProgressBar
                                        value={progress}
                                        max={100}
                                        label="Segmentando actividades..."
                                        showPercentage
                                    />
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </motion.div>
            )}

            {/* Segmentation Summary */}
            {segments && segments.length > 0 && (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                >
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <Card>
                            <CardContent className="p-4">
                                <p className="text-sm text-gray-600 dark:text-gray-400">Total Segmentos</p>
                                <p className="text-2xl font-bold text-primary-600">
                                    {formatNumber(segments.length)}
                                </p>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardContent className="p-4">
                                <p className="text-sm text-gray-600 dark:text-gray-400">Total Actividades</p>
                                <p className="text-2xl font-bold text-green-600">
                                    {formatNumber(segmentedData?.length || 0)}
                                </p>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardContent className="p-4">
                                <p className="text-sm text-gray-600 dark:text-gray-400">Promedio por Segmento</p>
                                <p className="text-2xl font-bold text-blue-600">
                                    {formatNumber(Math.round((segmentedData?.length || 0) / segments.length))}
                                </p>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardContent className="p-4">
                                <p className="text-sm text-gray-600 dark:text-gray-400">Segmento Mayor</p>
                                <p className="text-2xl font-bold text-purple-600">
                                    {formatNumber(Math.max(...segments.map(s => s.activity_count || 0)))}
                                </p>
                            </CardContent>
                        </Card>
                    </div>
                </motion.div>
            )}

            {/* Segments Visualization */}
            {segments && segments.length > 0 && (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                >
                    <Card>
                        <CardHeader>
                            <CardTitle>Segmentos Identificados</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-4">
                                {segments.map((segment, index) => (
                                    <div
                                        key={index}
                                        className="border-l-4 pl-4 py-3 rounded-r-lg bg-gray-50 dark:bg-gray-800"
                                        style={{ borderColor: getSegmentColor(index) }}
                                    >
                                        <div className="flex items-start justify-between">
                                            <div className="flex-1">
                                                <h3 className="font-semibold text-gray-900 dark:text-white mb-1">
                                                    Segmento {index + 1}: {segment.name || `Grupo ${index + 1}`}
                                                </h3>
                                                <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                                                    {segment.description || 'Sin descripción'}
                                                </p>
                                                <div className="flex items-center gap-4 text-sm">
                                                    <span className="text-gray-600 dark:text-gray-400">
                                                        <span className="font-medium">{segment.activity_count || 0}</span> actividades
                                                    </span>
                                                    {segment.time_total && (
                                                        <span className="text-gray-600 dark:text-gray-400">
                                                            <span className="font-medium">{segment.time_total}</span> min totales
                                                        </span>
                                                    )}
                                                </div>
                                            </div>
                                            <div
                                                className="w-12 h-12 rounded-full flex items-center justify-center text-white font-bold"
                                                style={{ backgroundColor: getSegmentColor(index) }}
                                            >
                                                {index + 1}
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </CardContent>
                    </Card>
                </motion.div>
            )}

            {/* Segmented Activities Table */}
            {segmentedData && segmentedData.length > 0 && (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                >
                    <Card>
                        <CardHeader>
                            <div className="flex justify-between items-center">
                                <CardTitle>Actividades Segmentadas</CardTitle>
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
                                            <th className="px-3 py-2 text-left font-semibold text-xs text-gray-700 dark:text-gray-300">Descripción</th>
                                            <th className="px-3 py-2 text-left font-semibold text-xs text-gray-700 dark:text-gray-300">Responsable</th>
                                            <th className="px-3 py-2 text-left font-semibold text-xs text-gray-700 dark:text-gray-300 min-w-[180px]">Clasificación Lean</th>
                                            <th className="px-3 py-2 text-left font-semibold text-xs text-gray-700 dark:text-gray-300">Tipo Desperdicio</th>
                                            <th className="px-3 py-2 text-left font-semibold text-xs text-gray-700 dark:text-gray-300">Justificación</th>
                                            <th className="px-3 py-2 text-left font-semibold text-xs text-gray-700 dark:text-gray-300">Tiempo (min)</th>
                                            <th className="px-3 py-2 text-left font-semibold text-xs text-gray-700 dark:text-gray-300">Tipo Actividad</th>
                                            <th className="px-3 py-2 text-left font-semibold text-xs text-gray-700 dark:text-gray-300">Automatizable</th>
                                            <th className="px-3 py-2 text-left font-semibold text-xs text-gray-700 dark:text-gray-300 min-w-[200px]">Sugerencia Automatización</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {segmentedData.map((row, index) => {
                                            const tipoActividad = row.tipo_actividad || row.tipo || 'Sin clasificar';
                                            const segmentIndex = segments.findIndex(s => s.name === tipoActividad);

                                            // Classification data
                                            const clasificacion = row['Clasificación Lean'] || row.clasificacion || row.classification || row.clasificacion_lean || 'N/A';
                                            const tipoDesperdicio = row['Tipo Desperdicio'] || row.tipo_desperdicio || row.desperdicio || '';
                                            const justificacion = row['Justificación'] || row.justificacion || 'N/A';

                                            // Automation data
                                            const automatizable = row.automatizable || row.Automatizable || 'No';
                                            const sugerenciaAutomatizacion = row.sugerencia_automatizacion || row.sugerencia_automatización || row['Sugerencia Automatización'] || '';

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
                                                        {clasificacion !== 'N/A' ? (
                                                            <span
                                                                className={`px-2 py-1 rounded-full text-xs font-medium text-white ${clasificacionColor}`}
                                                            >
                                                                {clasificacionText}
                                                            </span>
                                                        ) : (
                                                            <span className="text-gray-400 text-xs">N/A</span>
                                                        )}
                                                    </td>
                                                    <td className="px-3 py-2">
                                                        {tipoDesperdicio ? (
                                                            <span className="px-2 py-1 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300">
                                                                {tipoDesperdicio}
                                                            </span>
                                                        ) : (
                                                            <span className="text-gray-400 text-xs">-</span>
                                                        )}
                                                    </td>
                                                    <td className="px-3 py-2 text-gray-600 dark:text-gray-400 max-w-xs">
                                                        <div className="whitespace-normal break-words text-xs">
                                                            {justificacion}
                                                        </div>
                                                    </td>
                                                    <td className="px-3 py-2 text-gray-600 dark:text-gray-400 text-right">
                                                        {row['Tiempo Estándar'] || row.time || row.tiempo || '-'}
                                                    </td>
                                                    <td className="px-3 py-2">
                                                        <span
                                                            className="px-2 py-1 rounded-full text-xs font-medium text-white"
                                                            style={{ backgroundColor: getSegmentColor(segmentIndex >= 0 ? segmentIndex : 0) }}
                                                        >
                                                            {tipoActividad}
                                                        </span>
                                                    </td>
                                                    <td className="px-3 py-2">
                                                        {automatizable ? (
                                                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${automatizable.toLowerCase() === 'si' || automatizable.toLowerCase() === 'sí' ? 'bg-green-600 text-white' :
                                                                automatizable.toLowerCase() === 'posible' ? 'bg-yellow-600 text-white' :
                                                                    'bg-gray-600 text-white'
                                                                }`}>
                                                                {automatizable}
                                                            </span>
                                                        ) : (
                                                            <span className="text-gray-400 text-xs">-</span>
                                                        )}
                                                    </td>
                                                    <td className="px-3 py-2 text-gray-600 dark:text-gray-400">
                                                        <div className="whitespace-normal break-words text-xs max-w-[300px]">
                                                            {sugerenciaAutomatizacion || '-'}
                                                        </div>
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
        </div>
    );
}
