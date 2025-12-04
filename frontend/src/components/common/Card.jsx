/**
 * Card Component
 */
import { cn } from '../../utils/cn';

export default function Card({ children, className = '', ...props }) {
    return (
        <div
            className={cn(
                'bg-white dark:bg-dark-card rounded-lg shadow-md border border-gray-200 dark:border-dark-border',
                className
            )}
            {...props}
        >
            {children}
        </div>
    );
}

export function CardHeader({ children, className = '' }) {
    return (
        <div className={cn('px-6 py-4 border-b border-gray-200 dark:border-dark-border', className)}>
            {children}
        </div>
    );
}

export function CardTitle({ children, className = '' }) {
    return (
        <h3 className={cn('text-lg font-semibold text-gray-900 dark:text-white', className)}>
            {children}
        </h3>
    );
}

export function CardContent({ children, className = '' }) {
    return (
        <div className={cn('px-6 py-4', className)}>
            {children}
        </div>
    );
}

export function CardFooter({ children, className = '' }) {
    return (
        <div className={cn('px-6 py-4 border-t border-gray-200 dark:border-dark-border bg-gray-50 dark:bg-dark-bg rounded-b-lg', className)}>
            {children}
        </div>
    );
}
