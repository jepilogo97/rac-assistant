/**
 * Spinner Component
 */
import { Loader2 } from 'lucide-react';
import { cn } from '../../utils/cn';

export default function Spinner({ size = 'md', className = '' }) {
    const sizes = {
        sm: 'w-4 h-4',
        md: 'w-8 h-8',
        lg: 'w-12 h-12',
        xl: 'w-16 h-16',
    };

    return (
        <Loader2
            className={cn('animate-spin text-primary-600', sizes[size], className)}
        />
    );
}

export function LoadingOverlay({ message = 'Cargando...' }) {
    return (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
            <div className="bg-white dark:bg-dark-card rounded-lg p-8 shadow-2xl flex flex-col items-center gap-4">
                <Spinner size="xl" />
                <p className="text-lg font-medium text-gray-900 dark:text-white">{message}</p>
            </div>
        </div>
    );
}
