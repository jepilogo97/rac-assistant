import { useState, useRef } from 'react';
import { X, Save, Upload, FileText, Trash2, Key, BookOpen, Database } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import useStore from '../../store';
import Button from '../common/Button';
import toast from 'react-hot-toast';

export default function SettingsModal({ isOpen, onClose }) {
    const {
        apiKey, setApiKey,
        processContext, setProcessContext,
        ragFiles, setRagFiles
    } = useStore();

    const [tempApiKey, setTempApiKey] = useState(apiKey);
    const [tempContext, setTempContext] = useState(processContext || '');
    const [activeTab, setActiveTab] = useState('general');
    const fileInputRef = useRef(null);

    const handleSave = () => {
        setApiKey(tempApiKey);
        setProcessContext(tempContext);
        toast.success('Configuración guardada exitosamente');
        onClose();
    };

    const handleFileUpload = (e) => {
        const files = Array.from(e.target.files);
        const newFiles = files.map(file => ({
            name: file.name,
            size: file.size,
            type: file.type,
            lastModified: file.lastModified
        }));

        setRagFiles([...(ragFiles || []), ...newFiles]);
        toast.success(`${files.length} archivo(s) agregado(s) a la base de conocimiento`);
    };

    const removeFile = (index) => {
        const newFiles = [...ragFiles];
        newFiles.splice(index, 1);
        setRagFiles(newFiles);
    };

    if (!isOpen) return null;

    return (
        <AnimatePresence>
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
                <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.95 }}
                    className="bg-white dark:bg-dark-card rounded-xl shadow-2xl w-full max-w-2xl max-h-[85vh] overflow-hidden flex flex-col"
                >
                    {/* Header */}
                    <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-dark-border">
                        <h2 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                            <Database className="w-6 h-6 text-primary-600" />
                            Configuración del Proyecto
                        </h2>
                        <button
                            onClick={onClose}
                            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
                        >
                            <X className="w-5 h-5 text-gray-500" />
                        </button>
                    </div>

                    {/* Tabs */}
                    <div className="flex border-b border-gray-200 dark:border-dark-border">
                        <button
                            onClick={() => setActiveTab('general')}
                            className={`flex-1 px-6 py-3 text-sm font-medium transition-colors flex items-center justify-center gap-2 ${activeTab === 'general'
                                    ? 'text-primary-600 border-b-2 border-primary-600 bg-primary-50/50 dark:bg-primary-900/10'
                                    : 'text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800'
                                }`}
                        >
                            <Key className="w-4 h-4" />
                            API & Contexto
                        </button>
                        <button
                            onClick={() => setActiveTab('rag')}
                            className={`flex-1 px-6 py-3 text-sm font-medium transition-colors flex items-center justify-center gap-2 ${activeTab === 'rag'
                                    ? 'text-primary-600 border-b-2 border-primary-600 bg-primary-50/50 dark:bg-primary-900/10'
                                    : 'text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800'
                                }`}
                        >
                            <BookOpen className="w-4 h-4" />
                            Documentación (RAG)
                        </button>
                    </div>

                    {/* Content */}
                    <div className="flex-1 overflow-y-auto p-6">
                        {activeTab === 'general' ? (
                            <div className="space-y-6">
                                {/* API Key Section */}
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                        Google Gemini API Key
                                    </label>
                                    <div className="relative">
                                        <Key className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                                        <input
                                            type="password"
                                            value={tempApiKey}
                                            onChange={(e) => setTempApiKey(e.target.value)}
                                            placeholder="Ingresa tu API Key..."
                                            className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-dark-border rounded-lg bg-gray-50 dark:bg-dark-bg text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                                        />
                                    </div>
                                    <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                                        Necesaria para todas las funciones de IA.
                                        <a href="https://makersuite.google.com/app/apikey" target="_blank" rel="noreferrer" className="text-primary-600 hover:underline ml-1">
                                            Obtener Key
                                        </a>
                                    </p>
                                </div>

                                {/* Context Section */}
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                        Contexto del Proceso
                                    </label>
                                    <textarea
                                        value={tempContext}
                                        onChange={(e) => setTempContext(e.target.value)}
                                        placeholder="Describe el objetivo del proceso, problemas actuales, metas de mejora y cualquier información relevante que la IA deba conocer..."
                                        className="w-full h-40 p-4 border border-gray-300 dark:border-dark-border rounded-lg bg-gray-50 dark:bg-dark-bg text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
                                    />
                                    <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                                        Este contexto se utilizará en todas las generaciones (Segmentación, TO-BE, KPIs) para dar resultados más precisos.
                                    </p>
                                </div>
                            </div>
                        ) : (
                            <div className="space-y-6">
                                <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg border border-blue-100 dark:border-blue-800">
                                    <h4 className="font-semibold text-blue-800 dark:text-blue-300 mb-2 flex items-center gap-2">
                                        <BookOpen className="w-4 h-4" />
                                        Base de Conocimiento (RAG)
                                    </h4>
                                    <p className="text-sm text-blue-600 dark:text-blue-400">
                                        Sube documentos complementarios (PDF, TXT, DOCX) que contengan manuales, políticas o reglas de negocio. La IA consultará estos documentos para generar respuestas más alineadas a tu organización.
                                    </p>
                                </div>

                                {/* File Upload Area */}
                                <div
                                    className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-xl p-8 text-center hover:border-primary-500 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors cursor-pointer"
                                    onClick={() => fileInputRef.current?.click()}
                                >
                                    <Upload className="w-10 h-10 mx-auto text-gray-400 mb-3" />
                                    <p className="text-sm font-medium text-gray-900 dark:text-white">
                                        Haz clic para subir documentos
                                    </p>
                                    <p className="text-xs text-gray-500 mt-1">
                                        Soporta PDF, Word, Excel, TXT (Máx 10MB)
                                    </p>
                                    <input
                                        type="file"
                                        ref={fileInputRef}
                                        className="hidden"
                                        multiple
                                        onChange={handleFileUpload}
                                        accept=".pdf,.docx,.txt,.xlsx,.csv"
                                    />
                                </div>

                                {/* File List */}
                                {ragFiles && ragFiles.length > 0 && (
                                    <div className="space-y-2">
                                        <h5 className="text-sm font-medium text-gray-700 dark:text-gray-300">
                                            Documentos Cargados ({ragFiles.length})
                                        </h5>
                                        <div className="space-y-2 max-h-48 overflow-y-auto pr-2">
                                            {ragFiles.map((file, index) => (
                                                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
                                                    <div className="flex items-center gap-3 overflow-hidden">
                                                        <FileText className="w-5 h-5 text-primary-500 flex-shrink-0" />
                                                        <div className="truncate">
                                                            <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                                                                {file.name}
                                                            </p>
                                                            <p className="text-xs text-gray-500">
                                                                {(file.size / 1024).toFixed(1)} KB
                                                            </p>
                                                        </div>
                                                    </div>
                                                    <button
                                                        onClick={() => removeFile(index)}
                                                        className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                                                    >
                                                        <Trash2 className="w-4 h-4" />
                                                    </button>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>

                    {/* Footer */}
                    <div className="p-6 border-t border-gray-200 dark:border-dark-border flex justify-end gap-3 bg-gray-50 dark:bg-dark-bg/50">
                        <Button
                            variant="secondary"
                            onClick={onClose}
                        >
                            Cancelar
                        </Button>
                        <Button
                            icon={Save}
                            onClick={handleSave}
                        >
                            Guardar Configuración
                        </Button>
                    </div>
                </motion.div>
            </div>
        </AnimatePresence>
    );
}
