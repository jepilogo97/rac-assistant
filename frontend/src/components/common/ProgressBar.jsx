/**
 * ProgressBar Component
 */
import { motion } from 'framer-motion';
import { cn } from '../../utils/cn';

export default function ProgressBar({
    value = 0,
    max = 100,
    label = '',
    showPercentage = true,
    className = ''
}) {
    const percentage = Math.min(Math.max((value / max) * 100, 0), 100);

    return (
        <div className={cn('w-full', className)}>
            {(label || showPercentage) && (
                <div className="flex justify-between items-center mb-2">
                    {label && <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{label}</span>}
                    {showPercentage && <span className="text-sm font-medium text-primary-600">{percentage.toFixed(0)}%</span>}
                </div>
            )}
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5 overflow-hidden">
                <motion.div
                    className="h-full bg-gradient-to-r from-primary-500 to-primary-600 rounded-full"
                    initial={{ width: 0 }}
                    animate={{ width: `${percentage}%` }}
                    transition={{ duration: 0.5, ease: 'easeOut' }}
                />
            </div>
        </div>
    );
}
