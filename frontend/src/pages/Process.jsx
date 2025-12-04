/**
 * Process Page - BPMN Diagram Visualization and Editing
 */
import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Download, RefreshCw, Edit, Eye } from 'lucide-react';
import toast from 'react-hot-toast';
import useStore from '../store';
import endpoints from '../services/endpoints';
import Card, { CardHeader, CardTitle, CardContent } from '../components/common/Card';
import Button from '../components/common/Button';
import Spinner from '../components/common/Spinner';
import BpmnViewer from '../components/bpmn/BpmnViewer';
import BpmnModeler from '../components/bpmn/BpmnModeler';
import EmptyState from '../components/common/EmptyState';

export default function ProcessPage() {
    const {
        processData,
        validatedData,
        bpmnXml,
        activities,
        apiKey,
        setBpmnXml,
        setActivities,
        setValidatedData,
        loading,
        setLoading,
    } = useStore();

    const [viewMode, setViewMode] = useState('viewer');
    const [editableActivities, setEditableActivities] = useState([]);
    const [skipAutoGenerate, setSkipAutoGenerate] = useState(false);

    useEffect(() => {
        if ((validatedData || processData) && !bpmnXml && !skipAutoGenerate) {
            handleGenerateBPMN();
        }
    }, [validatedData, processData]);

    useEffect(() => {
        if (activities && activities.length > 0 && editableActivities.length === 0) {
            setEditableActivities(activities);
        }
    }, [activities]);

    const handleGenerateBPMN = async () => {
        const data = validatedData || processData;

        if (!data || data.length === 0) {
            toast.error('No hay datos para generar el diagrama BPMN');
            return;
        }

        setLoading('bpmn', true);

        try {
            const activitiesData = data.map((row, index) => ({
                id: `activity_${index + 1}`,
                name: row['Actividad'] || `Actividad ${index + 1}`,
                description: row['Descripción'] || '',
                responsible: row['Cargo que ejecuta la tarea'] || '',
                time: row['Tiempo Estándar'] || row['Tiempo Estándar (Min/Tarea)'] || row['Tiempo Promedio'] || row['Tiempo Prom (Min/Tarea)'] || row['time'] || row['tiempo'] || 0,
                automated: row['Tarea Automatizada'] === 'SI',
            }));

            const result = await endpoints.bpmn.generate(activitiesData, {
                pool_name: 'Proceso AS-IS',
                use_lanes: true,
                show_times: true,
            });

            if (result.success) {
                setBpmnXml(result.xml);
                setActivities(result.activities);
                setEditableActivities(result.activities);
                toast.success('Diagrama BPMN generado exitosamente');
            }
        } catch (error) {
            toast.error(error.message || 'Error al generar BPMN');
        } finally {
            setLoading('bpmn', false);
        }
    };

    const handleUpdateBPMN = async () => {
        if (!editableActivities || editableActivities.length === 0) {
            toast.error('No hay actividades para actualizar');
            return;
        }

        setLoading('bpmn', true);

        try {
            const result = await endpoints.bpmn.update(editableActivities, 'Proceso AS-IS');

            if (result.success) {
                setBpmnXml(result.xml);
                setActivities(editableActivities);

                setSkipAutoGenerate(true);

                const updatedValidatedData = editableActivities.map(activity => ({
                    'Actividad': activity.name,
                    'Descripción': activity.description || '',
                    'Cargo que ejecuta la tarea': activity.responsible,
                    'Tiempo Estándar': activity.time,
                    'Tarea Automatizada': activity.automated ? 'SI' : 'NO'
                }));
                setValidatedData(updatedValidatedData);

                toast.success('Diagrama BPMN actualizado');
            }
        } catch (error) {
            toast.error(error.message || 'Error al actualizar BPMN');
        } finally {
            setLoading('bpmn', false);
        }
    };

    const handleDownloadBPMN = () => {
        if (!bpmnXml) {
            toast.error('No hay diagrama BPMN para descargar');
            return;
        }

        const blob = new Blob([bpmnXml], { type: 'application/xml' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'proceso_asis.bpmn';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        toast.success('Diagrama BPMN descargado');
    };

    const handleActivityChange = (index, field, value) => {
        const updated = [...editableActivities];
        updated[index] = { ...updated[index], [field]: value };
        setEditableActivities(updated);
    };

    if (!processData && !validatedData) {
        return <EmptyState />;
    }

    return (
        <div className="space-y-6">
            <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex items-center justify-between"
            >
                <div>
                    <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
                        🔄 Diagrama BPMN
                    </h1>
                    <p className="text-gray-600 dark:text-gray-400">
                        Visualización y edición del proceso AS-IS
                    </p>
                </div>

                <div className="flex items-center gap-2">
                    <Button
                        variant="outline"
                        size="sm"
                        icon={viewMode === 'viewer' ? Edit : Eye}
                        onClick={() => {
                            const newMode = viewMode === 'viewer' ? 'editor' : 'viewer';
                            setViewMode(newMode);
                            if (newMode === 'editor' && activities && activities.length > 0) {
                                setEditableActivities([...activities]);
                            }
                        }}
                    >
                        {viewMode === 'viewer' ? 'Modo Edición' : 'Modo Vista'}
                    </Button>
                    <Button
                        variant="secondary"
                        size="sm"
                        icon={RefreshCw}
                        onClick={handleGenerateBPMN}
                        loading={loading.bpmn}
                    >
                        Regenerar
                    </Button>
                    <Button
                        variant="primary"
                        size="sm"
                        icon={Download}
                        onClick={handleDownloadBPMN}
                        disabled={!bpmnXml}
                    >
                        Descargar XML
                    </Button>
                </div>
            </motion.div>

            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
            >
                <Card>
                    <CardHeader>
                        <CardTitle>Diagrama de Proceso</CardTitle>
                    </CardHeader>
                    <CardContent>
                        {loading.bpmn ? (
                            <div className="h-96 flex items-center justify-center">
                                <Spinner size="lg" />
                            </div>
                        ) : bpmnXml ? (
                            viewMode === 'editor' ? (
                                <BpmnModeler
                                    xml={bpmnXml}
                                    height="600px"
                                    onXmlChange={(newXml) => setBpmnXml(newXml)}
                                />
                            ) : (
                                <BpmnViewer xml={bpmnXml} height="600px" />
                            )
                        ) : (
                            <div className="h-96 flex items-center justify-center">
                                <Button onClick={handleGenerateBPMN} loading={loading.bpmn}>
                                    Generar Diagrama BPMN
                                </Button>
                            </div>
                        )}
                    </CardContent>
                </Card>
            </motion.div>

            {viewMode === 'editor' && activities && activities.length > 0 && (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                >
                    <Card>
                        <CardHeader>
                            <div className="flex items-center justify-between">
                                <CardTitle>Editor de Actividades</CardTitle>
                                <Button size="sm" onClick={handleUpdateBPMN} loading={loading.bpmn}>
                                    Actualizar Diagrama
                                </Button>
                            </div>
                        </CardHeader>
                        <CardContent>
                            <div className="overflow-x-auto">
                                <table className="w-full text-sm">
                                    <thead className="bg-gray-50 dark:bg-gray-800">
                                        <tr>
                                            <th className="px-4 py-2 text-left font-semibold text-gray-700 dark:text-gray-300">ID</th>
                                            <th className="px-4 py-2 text-left font-semibold text-gray-700 dark:text-gray-300">Nombre</th>
                                            <th className="px-4 py-2 text-left font-semibold text-gray-700 dark:text-gray-300">Responsable</th>
                                            <th className="px-4 py-2 text-left font-semibold text-gray-700 dark:text-gray-300">Tiempo (min)</th>
                                            <th className="px-4 py-2 text-left font-semibold text-gray-700 dark:text-gray-300">Automatizada</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {editableActivities.map((activity, index) => (
                                            <tr key={activity.id} className="border-t border-gray-200 dark:border-gray-700">
                                                <td className="px-4 py-2 text-gray-600 dark:text-gray-400">
                                                    {activity.id}
                                                </td>
                                                <td className="px-4 py-2">
                                                    <input
                                                        type="text"
                                                        value={activity.name}
                                                        onChange={(e) => handleActivityChange(index, 'name', e.target.value)}
                                                        className="w-full px-2 py-1 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                                                    />
                                                </td>
                                                <td className="px-4 py-2">
                                                    <input
                                                        type="text"
                                                        value={activity.responsible}
                                                        onChange={(e) => handleActivityChange(index, 'responsible', e.target.value)}
                                                        className="w-full px-2 py-1 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                                                    />
                                                </td>
                                                <td className="px-4 py-2">
                                                    <input
                                                        type="number"
                                                        value={activity.time}
                                                        onChange={(e) => handleActivityChange(index, 'time', parseFloat(e.target.value))}
                                                        className="w-full px-2 py-1 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                                                    />
                                                </td>
                                                <td className="px-4 py-2">
                                                    <input
                                                        type="checkbox"
                                                        checked={activity.automated}
                                                        onChange={(e) => handleActivityChange(index, 'automated', e.target.checked)}
                                                        className="w-4 h-4"
                                                    />
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </CardContent>
                    </Card>
                </motion.div>
            )}

            {activities.length > 0 && (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                >
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <Card>
                            <CardContent className="p-4">
                                <p className="text-sm text-gray-600 dark:text-gray-400">Total Actividades</p>
                                <p className="text-2xl font-bold text-gray-900 dark:text-white">{activities.length}</p>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardContent className="p-4">
                                <p className="text-sm text-gray-600 dark:text-gray-400">Tiempo Total</p>
                                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                                    {activities.reduce((sum, a) => sum + (a.time || 0), 0).toFixed(1)} min
                                </p>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardContent className="p-4">
                                <p className="text-sm text-gray-600 dark:text-gray-400">Automatizadas</p>
                                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                                    {activities.filter(a => a.automated).length}
                                </p>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardContent className="p-4">
                                <p className="text-sm text-gray-600 dark:text-gray-400">Manuales</p>
                                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                                    {activities.filter(a => !a.automated).length}
                                </p>
                            </CardContent>
                        </Card>
                    </div>
                </motion.div>
            )}
        </div>
    );
}
