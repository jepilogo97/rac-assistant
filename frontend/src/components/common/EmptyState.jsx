import { motion } from 'framer-motion';
import { FileSpreadsheet, ArrowRight } from 'lucide-react';
import Button from './Button';

export default function EmptyState({
    title = "No hay datos disponibles",
    description = "Por favor, carga un archivo Excel para comenzar el análisis.",
    icon: Icon = FileSpreadsheet,
    actionLabel = "Ir a Carga de Datos",
    actionPath = "#upload",
    showAction = true
}) {
    const handleNavigate = () => {
        window.location.hash = actionPath;
    };

    return (
        <div className="flex items-center justify-center h-[60vh]">
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-center max-w-md mx-auto p-8 rounded-2xl bg-gray-50 dark:bg-gray-800/50 border border-gray-100 dark:border-gray-700"
            >
                <div className="bg-white dark:bg-gray-700 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6 shadow-sm">
                    <Icon className="w-10 h-10 text-gray-400 dark:text-gray-500" />
                </div>

                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-3">
                    {title}
                </h3>

                <p className="text-gray-500 dark:text-gray-400 mb-8 leading-relaxed">
                    {description}
                </p>

                {showAction && (
                    <Button
                        onClick={handleNavigate}
                        icon={ArrowRight}
                        className="w-full justify-center"
                    >
                        {actionLabel}
                    </Button>
                )}
            </motion.div>
        </div>
    );
}
