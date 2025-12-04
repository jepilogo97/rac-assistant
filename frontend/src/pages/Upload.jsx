/**
 * Upload Page - File upload and data preview
 */
import { useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import { Upload, FileSpreadsheet, CheckCircle, AlertCircle } from 'lucide-react';
import toast from 'react-hot-toast';
import useStore from '../store';
import endpoints from '../services/endpoints';
import Card, { CardHeader, CardTitle, CardContent } from '../components/common/Card';
import Button from '../components/common/Button';
import Spinner from '../components/common/Spinner';
import { formatFileSize, formatNumber, formatPercentage } from '../utils/formatters';
import { FILE_CONFIG } from '../utils/constants';

export default function UploadPage() {
    const {
        uploadedFile,
        processData,
        validationResult,
        apiKey,
        setUploadedFile,
        setProcessData,
        setValidationResult,
        setValidatedData,
        clearAllData,
        loading,
        setLoading,
    } = useStore();

    const [dragActive, setDragActive] = useState(false);

    const handleDrag = useCallback((e) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === 'dragenter' || e.type === 'dragover') {
            setDragActive(true);
        } else if (e.type === 'dragleave') {
            setDragActive(false);
        }
    }, []);

    const handleDrop = useCallback((e) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);

        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            handleFileUpload(e.dataTransfer.files[0]);
        }
    }, []);

    const handleFileChange = (e) => {
        if (e.target.files && e.target.files[0]) {
            handleFileUpload(e.target.files[0]);
        }
    };

    const handleFileUpload = async (file) => {
        // Validate file
        const fileExtension = file.name.split('.').pop().toLowerCase();
        if (!FILE_CONFIG.acceptedFormats.some(format => format.includes(fileExtension))) {
            toast.error('Formato de archivo no válido. Solo se aceptan archivos .xlsx o .xls');
            return;
        }

        if (file.size > FILE_CONFIG.maxSize) {
            toast.error(`El archivo excede el tamaño máximo de ${formatFileSize(FILE_CONFIG.maxSize)}`);
            return;
        }

        // Clear previous data
        clearAllData();
        setLoading('upload', true);

        try {
            const result = await endpoints.upload.uploadFile(file);

            if (result.success) {
                setUploadedFile(file);
                setProcessData(result.data);
                setValidationResult(result.validation);
                toast.success('Archivo cargado exitosamente');

                // Auto-validate if API key is available
                if (apiKey) {
                    await handleValidation(result.data);
                }
            } else {
                toast.error(result.error || 'Error al cargar el archivo');
            }
        } catch (error) {
            toast.error(error.message || 'Error al cargar el archivo');
        } finally {
            setLoading('upload', false);
        }
    };

    const handleValidation = async (data) => {
        if (!apiKey) {
            toast.error('Por favor configura tu API Key de Google Gemini');
            return;
        }

        setLoading('validation', true);

        try {
            const result = await endpoints.validation.validate(data || processData, apiKey);

            if (result.success) {
                setValidatedData(result.validated_data);
                toast.success('Datos validados correctamente');
            } else {
                toast.error('Error en la validación');
            }
        } catch (error) {
            toast.error(error.message || 'Error al validar datos');
        } finally {
            setLoading('validation', false);
        }
    };

    return (
        <div className="space-y-6">
            {/* Fixed Validation Overlay */}
            {loading.validation && (
                <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center">
                    <motion.div
                        initial={{ scale: 0.9, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl p-8 max-w-md mx-4"
                    >
                        <div className="flex flex-col items-center gap-4">
                            <Spinner size="lg" />
                            <div className="text-center">
                                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
                                    Validando datos
                                </h3>
                                <p className="text-gray-600 dark:text-gray-400">
                                    Por favor espera mientras validamos tu archivo...
                                </p>
                            </div>
                        </div>
                    </motion.div>
                </div>
            )}

            {/* Header */}
            <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-center"
            >
                <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
                    📂 Carga de Datos
                </h1>
                <p className="text-gray-600 dark:text-gray-400">
                    Sube tu archivo Excel y comienza el análisis de procesos
                </p>
            </motion.div>

            {/* Upload Card */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
            >
                <Card>
                    <CardHeader>
                        <CardTitle>⬆️ Selecciona tu archivo</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div
                            onDragEnter={handleDrag}
                            onDragLeave={handleDrag}
                            onDragOver={handleDrag}
                            onDrop={handleDrop}
                            className={`
                relative border-2 border-dashed rounded-lg text-center transition-all duration-200
                ${uploadedFile ? 'p-4' : 'p-12'}
                ${dragActive
                                    ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                                    : 'border-gray-300 dark:border-gray-600 hover:border-primary-400'
                                }
              `}
                        >
                            <input
                                type="file"
                                id="file-upload"
                                accept=".xlsx,.xls"
                                onChange={handleFileChange}
                                className="hidden"
                            />

                            {loading.upload || loading.validation ? (
                                <div className="flex flex-col items-center gap-4">
                                    <Spinner size="lg" />
                                    <p className="text-gray-600 dark:text-gray-400">
                                        {loading.validation ? 'Validando datos...' : 'Cargando archivo...'}
                                    </p>
                                </div>
                            ) : uploadedFile ? (
                                <div className="flex items-center justify-between gap-4">
                                    <div className="flex items-center gap-3 text-left">
                                        <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded-lg">
                                            <FileSpreadsheet className="w-6 h-6 text-green-600 dark:text-green-400" />
                                        </div>
                                        <div>
                                            <p className="font-medium text-gray-900 dark:text-white">
                                                {uploadedFile.name}
                                            </p>
                                            <p className="text-xs text-gray-500">
                                                {formatFileSize(uploadedFile.size)}
                                            </p>
                                        </div>
                                    </div>
                                    <label
                                        htmlFor="file-upload"
                                        className="text-sm text-primary-600 hover:text-primary-700 font-medium cursor-pointer hover:underline"
                                    >
                                        Cambiar archivo
                                    </label>
                                </div>
                            ) : (
                                <>
                                    <FileSpreadsheet className="w-16 h-16 mx-auto mb-4 text-primary-600" />
                                    <p className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                                        Arrastra y suelta tu archivo aquí
                                    </p>
                                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                                        o haz clic para seleccionar
                                    </p>
                                    <label
                                        htmlFor="file-upload"
                                        className="inline-flex items-center justify-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg font-medium transition-all duration-200 cursor-pointer focus-within:ring-2 focus-within:ring-primary-500 focus-within:ring-offset-2"
                                    >
                                        <Upload className="w-4 h-4" />
                                        Seleccionar Archivo
                                    </label>
                                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-4">
                                        Formatos: .xlsx, .xls • Tamaño máximo: {formatFileSize(FILE_CONFIG.maxSize)}
                                    </p>
                                </>
                            )}
                        </div>

                        {/* File Requirements */}
                        <div className="mt-6 grid md:grid-cols-2 gap-6">
                            <div>
                                <h4 className="font-semibold text-gray-900 dark:text-white mb-3">
                                    📋 Columnas Obligatorias (11 columnas)
                                </h4>
                                <ul className="space-y-1 text-sm text-gray-600 dark:text-gray-400">
                                    {FILE_CONFIG.expectedColumns.map((col, idx) => (
                                        <li key={idx} className="flex items-start gap-2">
                                            <span className="text-primary-600 mt-0.5">•</span>
                                            <span>{col}</span>
                                        </li>
                                    ))}
                                </ul>
                            </div>

                            <div className="bg-primary-50 dark:bg-primary-900/20 p-4 rounded-lg">
                                <h4 className="font-semibold text-gray-900 dark:text-white mb-2">
                                    💡 Información
                                </h4>
                                <ul className="space-y-2 text-sm text-gray-700 dark:text-gray-300">
                                    <li>✓ El archivo debe contener las 11 columnas requeridas</li>
                                    <li>✓ Los datos serán validados automáticamente</li>
                                    <li>✓ Se estimarán tiempos faltantes con IA</li>
                                </ul>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </motion.div>

            {/* Validation Result */}
            {validationResult && (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                >
                    <Card>
                        <CardHeader>
                            <CardTitle>
                                {validationResult.is_valid ? (
                                    <span className="flex items-center gap-2 text-green-600">
                                        <CheckCircle className="w-5 h-5" />
                                        Archivo Válido
                                    </span>
                                ) : (
                                    <span className="flex items-center gap-2 text-red-600">
                                        <AlertCircle className="w-5 h-5" />
                                        Errores de Validación
                                    </span>
                                )}
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            {validationResult.errors && validationResult.errors.length > 0 && (
                                <div className="mb-4">
                                    <h4 className="font-semibold text-red-600 mb-2">Errores:</h4>
                                    <ul className="space-y-1">
                                        {validationResult.errors.map((error, idx) => (
                                            <li key={idx} className="text-sm text-red-600">• {error}</li>
                                        ))}
                                    </ul>
                                </div>
                            )}

                            {validationResult.warnings && validationResult.warnings.length > 0 && (
                                <div className="mb-4">
                                    <h4 className="font-semibold text-yellow-600 mb-2">Advertencias:</h4>
                                    <ul className="space-y-1">
                                        {validationResult.warnings.map((warning, idx) => (
                                            <li key={idx} className="text-sm text-yellow-600">• {warning}</li>
                                        ))}
                                    </ul>
                                </div>
                            )}

                            {validationResult.suggestions && validationResult.suggestions.length > 0 && (
                                <div>
                                    <h4 className="font-semibold text-blue-600 mb-2">Sugerencias:</h4>
                                    <ul className="space-y-1">
                                        {validationResult.suggestions.map((suggestion, idx) => (
                                            <li key={idx} className="text-sm text-blue-600">• {suggestion}</li>
                                        ))}
                                    </ul>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </motion.div>
            )}

            {/* Data Preview */}
            {processData && (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                >
                    {/* File Name Title */}
                    {uploadedFile && (
                        <div className="text-center mb-4">
                            <h3 className="text-xl font-bold text-gray-900 dark:text-white flex items-center justify-center gap-2">
                                <span className="text-2xl">📄</span>
                                <span>{uploadedFile.name}</span>
                            </h3>
                            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                                {formatFileSize(uploadedFile.size)} • {formatNumber(processData.length)} filas • {processData.length > 0 ? Object.keys(processData[0]).length : 0} columnas
                            </p>
                        </div>
                    )}

                    <Card>
                        <CardHeader>
                            <CardTitle>👀 Vista Previa de Datos</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                                <div className="bg-primary-50 dark:bg-primary-900/20 p-4 rounded-lg">
                                    <p className="text-sm text-gray-600 dark:text-gray-400">Total Filas</p>
                                    <p className="text-2xl font-bold text-primary-600">{formatNumber(processData.length)}</p>
                                </div>
                                <div className="bg-green-50 dark:bg-green-900/20 p-4 rounded-lg">
                                    <p className="text-sm text-gray-600 dark:text-gray-400">Columnas</p>
                                    <p className="text-2xl font-bold text-green-600">
                                        {processData.length > 0 ? Object.keys(processData[0]).length : 0}
                                    </p>
                                </div>
                                <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
                                    <p className="text-sm text-gray-600 dark:text-gray-400">Archivo</p>
                                    <p className="text-sm font-medium text-blue-600 truncate">
                                        {uploadedFile?.name}
                                    </p>
                                </div>
                                <div className="bg-purple-50 dark:bg-purple-900/20 p-4 rounded-lg">
                                    <p className="text-sm text-gray-600 dark:text-gray-400">Tamaño</p>
                                    <p className="text-sm font-medium text-purple-600">
                                        {uploadedFile && formatFileSize(uploadedFile.size)}
                                    </p>
                                </div>
                            </div>

                            {/* Column Summary */}
                            <div className="mb-6">
                                <h4 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                                    <span className="text-2xl">📊</span>
                                    <span>Resumen Detallado por Columna</span>
                                </h4>
                                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                                    {processData.length > 0 && Object.keys(processData[0]).map((column) => {
                                        const values = processData.map(row => row[column]).filter(v => v !== null && v !== undefined && v !== '');
                                        const uniqueCount = new Set(values).size;
                                        const nullCount = processData.length - values.length;
                                        const completeness = (values.length / processData.length) * 100;

                                        // Determine completeness color
                                        let completenessColor = 'bg-red-500';
                                        let completenessTextColor = 'text-red-600';
                                        let completenessIcon = '❌';

                                        if (completeness === 100) {
                                            completenessColor = 'bg-green-500';
                                            completenessTextColor = 'text-green-600';
                                            completenessIcon = '✅';
                                        } else if (completeness >= 80) {
                                            completenessColor = 'bg-yellow-500';
                                            completenessTextColor = 'text-yellow-600';
                                            completenessIcon = '⚠️';
                                        }

                                        return (
                                            <div
                                                key={column}
                                                className="bg-white dark:bg-gray-800 p-4 rounded-lg border-2 border-gray-200 dark:border-gray-700 hover:border-primary-400 dark:hover:border-primary-600 transition-all duration-200 shadow-sm hover:shadow-md"
                                            >
                                                {/* Column Name */}
                                                <div className="flex items-start justify-between mb-3">
                                                    <p className="font-bold text-gray-900 dark:text-white text-sm break-words pr-2" title={column}>
                                                        {column}
                                                    </p>
                                                    <span className="text-lg flex-shrink-0">{completenessIcon}</span>
                                                </div>

                                                {/* Statistics Grid */}
                                                <div className="space-y-2 mb-3">
                                                    <div className="flex items-center justify-between text-xs">
                                                        <span className="text-gray-600 dark:text-gray-400 flex items-center gap-1">
                                                            <span className="text-blue-500">🔢</span>
                                                            Valores únicos
                                                        </span>
                                                        <span className="font-semibold text-blue-600 dark:text-blue-400">
                                                            {formatNumber(uniqueCount)}
                                                        </span>
                                                    </div>

                                                    <div className="flex items-center justify-between text-xs">
                                                        <span className="text-gray-600 dark:text-gray-400 flex items-center gap-1">
                                                            <span className="text-gray-500">⭕</span>
                                                            Valores vacíos
                                                        </span>
                                                        <span className="font-semibold text-gray-600 dark:text-gray-400">
                                                            {formatNumber(nullCount)}
                                                        </span>
                                                    </div>

                                                    <div className="flex items-center justify-between text-xs">
                                                        <span className="text-gray-600 dark:text-gray-400 flex items-center gap-1">
                                                            <span className={completenessTextColor}>📈</span>
                                                            Completitud
                                                        </span>
                                                        <span className={`font-bold ${completenessTextColor}`}>
                                                            {formatPercentage(completeness)}
                                                        </span>
                                                    </div>
                                                </div>

                                                {/* Progress Bar */}
                                                <div className="space-y-1">
                                                    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 overflow-hidden">
                                                        <div
                                                            className={`h-2 rounded-full transition-all duration-500 ${completenessColor}`}
                                                            style={{ width: `${completeness}%` }}
                                                        />
                                                    </div>
                                                    <p className="text-xs text-gray-500 dark:text-gray-500 text-center">
                                                        {formatNumber(values.length)} de {formatNumber(processData.length)} completos
                                                    </p>
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>

                            {/* Data Table - Show ALL rows */}
                            <div>
                                <h4 className="font-semibold text-gray-900 dark:text-white mb-3">
                                    📋 Datos Completos ({formatNumber(processData.length)} filas)
                                </h4>
                                <div className="overflow-x-auto max-h-96 overflow-y-auto border border-gray-200 dark:border-gray-700 rounded-lg">
                                    <table className="w-full text-sm">
                                        <thead className="bg-gray-50 dark:bg-gray-800 sticky top-0">
                                            <tr>
                                                <th className="px-4 py-2 text-left font-semibold text-gray-700 dark:text-gray-300 border-b border-gray-200 dark:border-gray-700">
                                                    #
                                                </th>
                                                {processData.length > 0 && Object.keys(processData[0]).map((key) => (
                                                    <th key={key} className="px-4 py-2 text-left font-semibold text-gray-700 dark:text-gray-300 border-b border-gray-200 dark:border-gray-700">
                                                        {key}
                                                    </th>
                                                ))}
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {processData.map((row, idx) => (
                                                <tr key={idx} className="border-t border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800">
                                                    <td className="px-4 py-2 text-gray-500 dark:text-gray-400 font-medium">
                                                        {idx + 1}
                                                    </td>
                                                    {Object.values(row).map((value, vidx) => (
                                                        <td key={vidx} className="px-4 py-2 text-gray-600 dark:text-gray-400">
                                                            {value}
                                                        </td>
                                                    ))}
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </motion.div>
            )}
        </div>
    );
}
