/**
 * KPIs Page - Modern Metrics and Analytics Dashboard
 */
import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Play, TrendingUp, Clock, Zap, Target, Activity, Award, BarChart3, PieChart, GitCompare } from 'lucide-react';
import toast from 'react-hot-toast';
import useStore from '../store';
import endpoints from '../services/endpoints';
import Card, { CardHeader, CardTitle, CardContent } from '../components/common/Card';
import Button from '../components/common/Button';
import ProgressBar from '../components/common/ProgressBar';
import { formatNumber, formatPercentage, formatTime } from '../utils/formatters';
import EmptyState from '../components/common/EmptyState';

// Circular Progress Component
const CircularProgress = ({ value, max = 100, size = 120, strokeWidth = 8, color = "blue", label, sublabel }) => {
    const radius = (size - strokeWidth) / 2;
    const circumference = radius * 2 * Math.PI;
    const percentage = (value / max) * 100;
    const offset = circumference - (percentage / 100) * circumference;

    const colorClasses = {
        blue: 'text-blue-600',
        green: 'text-green-600',
        purple: 'text-purple-600',
        orange: 'text-orange-600',
        red: 'text-red-600',
    };

    const strokeClasses = {
        blue: 'stroke-blue-600',
        green: 'stroke-green-600',
        purple: 'stroke-purple-600',
        orange: 'stroke-orange-600',
        red: 'stroke-red-600',
    };

    return (
        <div className="flex flex-col items-center">
            <div className="relative" style={{ width: size, height: size }}>
                <svg className="transform -rotate-90" width={size} height={size}>
                    <circle
                        className="stroke-gray-200 dark:stroke-gray-700"
                        strokeWidth={strokeWidth}
                        fill="transparent"
                        r={radius}
                        cx={size / 2}
                        cy={size / 2}
                    />
                    <motion.circle
                        className={strokeClasses[color]}
                        strokeWidth={strokeWidth}
                        strokeLinecap="round"
                        fill="transparent"
                        r={radius}
                        cx={size / 2}
                        cy={size / 2}
                        initial={{ strokeDashoffset: circumference }}
                        animate={{ strokeDashoffset: offset }}
                        transition={{ duration: 1, ease: "easeOut" }}
                        style={{
                            strokeDasharray: `${circumference} ${circumference}`,
                        }}
                    />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <span className={`text-2xl font-bold ${colorClasses[color]}`}>
                        {Math.round(percentage)}%
                    </span>
                    {sublabel && (
                        <span className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                            {sublabel}
                        </span>
                    )}
                </div>
            </div>
            {label && (
                <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mt-3 text-center">
                    {label}
                </p>
            )}
        </div>
    );
};

// Modern KPI Card Component
const ModernKPICard = ({ icon: Icon, title, value, subtitle, color = "blue", trend, gradient }) => {
    const gradients = {
        blue: 'from-blue-500 to-blue-600',
        green: 'from-green-500 to-green-600',
        purple: 'from-purple-500 to-purple-600',
        orange: 'from-orange-500 to-orange-600',
        red: 'from-red-500 to-red-600',
        cyan: 'from-cyan-500 to-cyan-600',
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            whileHover={{ y: -5, transition: { duration: 0.2 } }}
            className="relative overflow-hidden rounded-xl bg-white dark:bg-gray-800 shadow-lg"
        >
            {/* Gradient Background */}
            <div className={`absolute inset-0 bg-gradient-to-br ${gradients[color]} opacity-5`} />

            {/* Content */}
            <div className="relative p-6">
                <div className="flex items-start justify-between mb-4">
                    <div className={`p-3 bg-gradient-to-br ${gradients[color]} rounded-lg shadow-lg`}>
                        <Icon className="w-6 h-6 text-white" />
                    </div>
                    {trend && (
                        <div className={`flex items-center gap-1 text-sm font-semibold ${trend > 0 ? 'text-green-600' : 'text-red-600'
                            }`}>
                            <TrendingUp className={`w-4 h-4 ${trend < 0 ? 'rotate-180' : ''}`} />
                            {Math.abs(trend).toFixed(1)}%
                        </div>
                    )}
                </div>

                <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
                    {title}
                </h3>

                <p className="text-3xl font-bold text-gray-900 dark:text-white mb-1">
                    {value}
                </p>

                {subtitle && (
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                        {subtitle}
                    </p>
                )}
            </div>
        </motion.div>
    );
};

export default function KPIsPage() {
    const {
        processData,
        validatedData,
        classifiedData,
        tobeData,
        tobeProposals,
        tobeComparison,
        kpisData,
        apiKey,
        setKpisData,
        loading,
        setLoading,
    } = useStore();

    const [progress, setProgress] = useState(0);

    const handleAnalyzeKPIs = async () => {
        const asisData = validatedData || processData;

        if (!asisData || asisData.length === 0) {
            toast.error('No hay datos para analizar');
            return;
        }

        // Validate that TO-BE process has been generated
        if (!tobeData || tobeData.length === 0) {
            toast.error('Primero debes generar el Proceso Sugerido (TO-BE) antes de analizar KPIs');
            return;
        }

        if (!apiKey) {
            toast.error('Por favor configura tu API Key de Google Gemini');
            return;
        }

        setLoading('kpis', true);
        setProgress(0);

        try {
            // Simulate progress
            const progressInterval = setInterval(() => {
                setProgress(prev => Math.min(prev + 12, 90));
            }, 600);

            const result = await endpoints.kpis.analyze(
                asisData,
                tobeData,
                classifiedData,
                apiKey
            );

            clearInterval(progressInterval);
            setProgress(100);

            if (result.success) {
                setKpisData(result);
                toast.success('Análisis de KPIs completado');
            }
        } catch (error) {
            toast.error(error.message || 'Error al analizar KPIs');
        } finally {
            setLoading('kpis', false);
            setTimeout(() => setProgress(0), 1000);
        }
    };

    useEffect(() => {
        // Auto-analyze if data is available AND TO-BE process exists
        if ((validatedData || processData) && tobeData && !kpisData && apiKey) {
            handleAnalyzeKPIs();
        }
    }, [validatedData, processData, tobeData, apiKey]);

    if (!processData && !validatedData) {
        return <EmptyState />;
    }

    const metrics = kpisData?.metrics || {};
    const asisMetrics = metrics.asis || {};
    const tobeMetrics = metrics.tobe || {};
    const improvements = metrics.improvements || {};
    const wasteAnalysis = metrics.waste_analysis || {};

    // Calculate KPI values
    const totalActivities = asisMetrics.total_activities || 0;
    const totalTime = asisMetrics.total_time || 0;
    const automatedCount = asisMetrics.automated_count || 0;
    const avgTime = asisMetrics.avg_time_per_activity || 0;
    const wastePercentage = wasteAnalysis.waste_percentage || 0;

    // Calculate efficiency score (0-100)
    const efficiencyScore = totalActivities > 0
        ? Math.min(100, ((automatedCount / totalActivities) * 50) + ((100 - wastePercentage) * 0.5))
        : 0;

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
                        📊 KPIs y Métricas
                    </h1>
                    <p className="text-gray-600 dark:text-gray-400">
                        Dashboard de indicadores clave de desempeño del proceso
                    </p>
                </div>

                <Button
                    icon={Play}
                    onClick={handleAnalyzeKPIs}
                    loading={loading.kpis}
                >
                    {kpisData ? 'Actualizar Análisis' : 'Analizar KPIs'}
                </Button>
            </motion.div>

            {/* Loading State */}
            {loading.kpis && progress > 0 && (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                >
                    <Card>
                        <CardContent className="py-8">
                            <ProgressBar
                                value={progress}
                                max={100}
                                label="Analizando métricas y generando insights con IA..."
                                showPercentage
                            />
                        </CardContent>
                    </Card>
                </motion.div>
            )}

            {/* Main KPIs - 5 Modern Cards */}
            {kpisData && (
                <>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                        {/* KPI 1: Reducción de Tiempo Total */}
                        <ModernKPICard
                            icon={Clock}
                            title="Reducción Tiempo Total"
                            value={formatTime(tobeComparison?.improvements?.time_reduction || 0)}
                            subtitle="Tiempo total ahorrado"
                            color="blue"
                            trend={tobeComparison?.improvements?.time_reduction_pct ? -tobeComparison.improvements.time_reduction_pct : null}
                        />

                        {/* KPI 2: Reducción de Personal */}
                        <ModernKPICard
                            icon={Target}
                            title="Reducción de Personal"
                            value={(() => {
                                if (!tobeProposals || !Array.isArray(tobeProposals)) return "0";
                                const reduction = tobeProposals.reduce((acc, curr) => {
                                    const original = Number(curr.personas_originales) || 0;
                                    const improved = Number(curr.personas_mejoradas) || 0;
                                    return acc + (original - improved);
                                }, 0);
                                return formatNumber(reduction);
                            })()}
                            subtitle="Personas liberadas"
                            color="purple"
                        />

                        {/* KPI 3: Actividades Optimizadas/Eliminadas */}
                        <ModernKPICard
                            icon={Zap}
                            title="Activ. Optimizadas/Elim."
                            value={(() => {
                                if (!tobeProposals || !Array.isArray(tobeProposals)) return "0";
                                return formatNumber(
                                    tobeProposals.filter(p =>
                                        ['Optimizada', 'Eliminada', 'Automatizada', 'Combinada'].includes(p.accion)
                                    ).length
                                );
                            })()}
                            subtitle={`De ${formatNumber(tobeProposals?.length || 0)} totales`}
                            color="green"
                        />

                        {/* KPI 4: Reducción de Tiempo por Actividad */}
                        <ModernKPICard
                            icon={Activity}
                            title="Reducción Promedio"
                            value={(() => {
                                const totalReduction = tobeComparison?.improvements?.time_reduction || 0;
                                const count = tobeComparison?.comparison?.asis?.total_activities || 1;
                                return formatTime(totalReduction / count);
                            })()}
                            subtitle="Por actividad"
                            color="orange"
                        />
                    </div>

                    {/* AS-IS vs TO-BE Comparison */}
                    {tobeComparison && (
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                        >
                            <Card>
                                <CardHeader>
                                    <CardTitle className="flex items-center gap-2">
                                        <GitCompare className="w-5 h-5 text-primary-600" />
                                        Comparación: Proceso Actual vs Proceso Propuesto
                                    </CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <div className="grid md:grid-cols-2 gap-8">
                                        {/* AS-IS (Proceso Actual) */}
                                        <div className="space-y-4">
                                            <div className="flex items-center gap-2 mb-4">
                                                <div className="w-3 h-3 bg-gray-500 rounded-full"></div>
                                                <h3 className="text-lg font-bold text-gray-900 dark:text-white">
                                                    Proceso Actual (AS-IS)
                                                </h3>
                                            </div>

                                            <div className="space-y-3">
                                                <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                                                    <span className="text-sm text-gray-600 dark:text-gray-400">Total Actividades:</span>
                                                    <span className="text-lg font-bold text-gray-900 dark:text-white">
                                                        {formatNumber(tobeComparison.comparison?.asis?.total_activities || 0)}
                                                    </span>
                                                </div>

                                                <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                                                    <span className="text-sm text-gray-600 dark:text-gray-400">Tiempo Total:</span>
                                                    <span className="text-lg font-bold text-gray-900 dark:text-white">
                                                        {formatTime(tobeComparison.comparison?.asis?.total_time || 0)}
                                                    </span>
                                                </div>

                                                <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                                                    <span className="text-sm text-gray-600 dark:text-gray-400">Personal Requerido:</span>
                                                    <span className="text-lg font-bold text-gray-900 dark:text-white">
                                                        {(() => {
                                                            if (!tobeProposals || !Array.isArray(tobeProposals)) return "0";
                                                            const totalPersonnel = tobeProposals.reduce((acc, curr) => {
                                                                return acc + (Number(curr.personas_originales) || 0);
                                                            }, 0);
                                                            return formatNumber(totalPersonnel);
                                                        })()}
                                                    </span>
                                                </div>

                                                <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                                                    <span className="text-sm text-gray-600 dark:text-gray-400">Tiempo Promedio/Act.:</span>
                                                    <span className="text-lg font-bold text-gray-900 dark:text-white">
                                                        {(() => {
                                                            const totalTime = tobeComparison.comparison?.asis?.total_time || 0;
                                                            const totalActivities = tobeComparison.comparison?.asis?.total_activities || 1;
                                                            return formatTime(totalTime / totalActivities);
                                                        })()}
                                                    </span>
                                                </div>

                                                <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                                                    <span className="text-sm text-gray-600 dark:text-gray-400">Automatizadas:</span>
                                                    <span className="text-lg font-bold text-gray-900 dark:text-white">
                                                        {formatNumber(tobeComparison.comparison?.asis?.automated_activities || 0)}
                                                    </span>
                                                </div>
                                            </div>
                                        </div>

                                        {/* TO-BE (Proceso Propuesto) */}
                                        <div className="space-y-4">
                                            <div className="flex items-center gap-2 mb-4">
                                                <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                                                <h3 className="text-lg font-bold text-gray-900 dark:text-white">
                                                    Proceso Propuesto (TO-BE)
                                                </h3>
                                            </div>

                                            <div className="space-y-3">
                                                <div className="flex justify-between items-center p-3 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
                                                    <span className="text-sm text-gray-600 dark:text-gray-400">Total Actividades:</span>
                                                    <span className="text-lg font-bold text-green-600">
                                                        {formatNumber(tobeComparison.comparison?.tobe?.total_activities || 0)}
                                                    </span>
                                                </div>

                                                <div className="flex justify-between items-center p-3 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
                                                    <span className="text-sm text-gray-600 dark:text-gray-400">Tiempo Total:</span>
                                                    <span className="text-lg font-bold text-green-600">
                                                        {formatTime(tobeComparison.comparison?.tobe?.total_time || 0)}
                                                    </span>
                                                </div>

                                                <div className="flex justify-between items-center p-3 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
                                                    <span className="text-sm text-gray-600 dark:text-gray-400">Personal Requerido:</span>
                                                    <span className="text-lg font-bold text-green-600">
                                                        {(() => {
                                                            if (!tobeProposals || !Array.isArray(tobeProposals)) return "0";
                                                            const totalPersonnel = tobeProposals.reduce((acc, curr) => {
                                                                return acc + (Number(curr.personas_mejoradas) || 0);
                                                            }, 0);
                                                            return formatNumber(totalPersonnel);
                                                        })()}
                                                    </span>
                                                </div>

                                                <div className="flex justify-between items-center p-3 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
                                                    <span className="text-sm text-gray-600 dark:text-gray-400">Tiempo Promedio/Act.:</span>
                                                    <span className="text-lg font-bold text-green-600">
                                                        {(() => {
                                                            const totalTime = tobeComparison.comparison?.tobe?.total_time || 0;
                                                            const totalActivities = tobeComparison.comparison?.tobe?.total_activities || 1;
                                                            return formatTime(totalTime / totalActivities);
                                                        })()}
                                                    </span>
                                                </div>

                                                <div className="flex justify-between items-center p-3 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
                                                    <span className="text-sm text-gray-600 dark:text-gray-400">Automatizadas:</span>
                                                    <span className="text-lg font-bold text-green-600">
                                                        {formatNumber(tobeComparison.comparison?.tobe?.automated_activities || 0)}
                                                    </span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        </motion.div>
                    )}


                    {/* Improvements (if TO-BE exists) */}
                    {tobeComparison?.improvements && (
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                        >
                            <Card>
                                <CardHeader>
                                    <CardTitle className="flex items-center gap-2">
                                        <TrendingUp className="w-5 h-5 text-green-600" />
                                        Mejoras Proyectadas (TO-BE)
                                    </CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
                                        <div className="text-center p-6 bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 rounded-xl">
                                            <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Reducción de Tiempo</p>
                                            <p className="text-4xl font-bold text-green-600 mb-1">
                                                {formatPercentage(tobeComparison.improvements.time_reduction_pct || 0)}
                                            </p>
                                            <p className="text-xs text-gray-500">
                                                {formatTime(tobeComparison.improvements.time_reduction || 0)} ahorrados
                                            </p>
                                        </div>

                                        <div className="text-center p-6 bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 rounded-xl">
                                            <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Actividades Eliminadas</p>
                                            <p className="text-4xl font-bold text-blue-600 mb-1">
                                                {formatNumber(tobeComparison.improvements.activities_reduction || 0)}
                                            </p>
                                            <p className="text-xs text-gray-500">
                                                {formatPercentage((tobeComparison.improvements.activities_reduction / (tobeComparison.comparison?.asis?.total_activities || 1)) * 100 || 0)} del total
                                            </p>
                                        </div>

                                        <div className="text-center p-6 bg-gradient-to-br from-orange-50 to-orange-100 dark:from-orange-900/20 dark:to-orange-800/20 rounded-xl">
                                            <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Actividades Optimizadas</p>
                                            <p className="text-4xl font-bold text-orange-600 mb-1">
                                                {(() => {
                                                    if (!tobeProposals || !Array.isArray(tobeProposals)) return "0";
                                                    return formatNumber(
                                                        tobeProposals.filter(p =>
                                                            ['Optimizada', 'Combinada'].includes(p.accion)
                                                        ).length
                                                    );
                                                })()}
                                            </p>
                                            <p className="text-xs text-gray-500">
                                                actividades mejoradas
                                            </p>
                                        </div>

                                        <div className="text-center p-6 bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/20 rounded-xl">
                                            <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Aumento Automatización</p>
                                            <p className="text-4xl font-bold text-purple-600 mb-1">
                                                +{formatNumber(tobeComparison.improvements.automation_increase || 0)}
                                            </p>
                                            <p className="text-xs text-gray-500">
                                                actividades automatizadas
                                            </p>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        </motion.div>
                    )}

                    {/* Waste Analysis */}
                    {wasteAnalysis.total_waste_activities > 0 && (
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                        >
                            <Card>
                                <CardHeader>
                                    <CardTitle className="flex items-center gap-2">
                                        <BarChart3 className="w-5 h-5 text-red-600" />
                                        Análisis de Desperdicios
                                    </CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <div className="grid md:grid-cols-3 gap-6 mb-6">
                                        <div className="text-center p-6 bg-gradient-to-br from-red-50 to-red-100 dark:from-red-900/20 dark:to-red-800/20 rounded-xl">
                                            <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Actividades con Desperdicio</p>
                                            <p className="text-4xl font-bold text-red-600">
                                                {formatNumber(wasteAnalysis.total_waste_activities || 0)}
                                            </p>
                                        </div>

                                        <div className="text-center p-6 bg-gradient-to-br from-orange-50 to-orange-100 dark:from-orange-900/20 dark:to-orange-800/20 rounded-xl">
                                            <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Porcentaje de Desperdicio</p>
                                            <p className="text-4xl font-bold text-orange-600">
                                                {formatPercentage(wastePercentage)}
                                            </p>
                                        </div>

                                        <div className="text-center p-6 bg-gradient-to-br from-yellow-50 to-yellow-100 dark:from-yellow-900/20 dark:to-yellow-800/20 rounded-xl">
                                            <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Tipos de Desperdicio</p>
                                            <p className="text-4xl font-bold text-yellow-600">
                                                {Object.keys(wasteAnalysis.waste_by_type || {}).length}
                                            </p>
                                        </div>
                                    </div>

                                    {wasteAnalysis.waste_by_type && (
                                        <div>
                                            <h4 className="font-semibold text-gray-900 dark:text-white mb-4">
                                                Distribución por Tipo
                                            </h4>
                                            <div className="space-y-3">
                                                {Object.entries(wasteAnalysis.waste_by_type).map(([type, count]) => {
                                                    const percentage = (count / totalActivities) * 100;
                                                    return (
                                                        <div key={type} className="flex items-center gap-3">
                                                            <span className="text-sm font-medium text-gray-700 dark:text-gray-300 w-40">
                                                                {type}
                                                            </span>
                                                            <div className="flex-1">
                                                                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                                                                    <motion.div
                                                                        className="h-3 bg-gradient-to-r from-red-500 to-orange-500 rounded-full"
                                                                        initial={{ width: 0 }}
                                                                        animate={{ width: `${percentage}%` }}
                                                                        transition={{ duration: 1, ease: "easeOut" }}
                                                                    />
                                                                </div>
                                                            </div>
                                                            <span className="text-sm font-semibold text-gray-600 dark:text-gray-400 w-24 text-right">
                                                                {count} ({formatPercentage(percentage, 1)})
                                                            </span>
                                                        </div>
                                                    );
                                                })}
                                            </div>
                                        </div>
                                    )}
                                </CardContent>
                            </Card>
                        </motion.div>
                    )}

                    {/* AI Insights */}
                    {kpisData.insights && kpisData.insights.length > 0 && (
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                        >
                            <Card>
                                <CardHeader>
                                    <CardTitle>💡 Insights Generados por IA</CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <div className="grid md:grid-cols-2 gap-4">
                                        {kpisData.insights.map((insight, index) => (
                                            <motion.div
                                                key={index}
                                                initial={{ opacity: 0, x: -20 }}
                                                animate={{ opacity: 1, x: 0 }}
                                                transition={{ delay: index * 0.1 }}
                                                className="flex items-start gap-3 p-4 bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-lg border border-blue-200 dark:border-blue-800"
                                            >
                                                <div className="flex-shrink-0 w-8 h-8 bg-gradient-to-br from-blue-600 to-indigo-600 text-white rounded-full flex items-center justify-center text-sm font-bold shadow-lg">
                                                    {index + 1}
                                                </div>
                                                <p className="text-sm text-gray-700 dark:text-gray-300 flex-1 leading-relaxed">
                                                    {insight}
                                                </p>
                                            </motion.div>
                                        ))}
                                    </div>
                                </CardContent>
                            </Card>
                        </motion.div>
                    )}
                </>
            )}
        </div>
    );
}
