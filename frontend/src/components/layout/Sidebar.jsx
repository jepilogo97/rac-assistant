/**
 * Sidebar Component
 */
import {
    Upload, GitBranch, Tags, Layers, Target, BarChart3,
    X, Menu, Rocket
} from 'lucide-react';
import { cn } from '../../utils/cn';
import { APP_NAME } from '../../utils/constants';

const iconMap = {
    Upload, GitBranch, Tags, Layers, Target, BarChart3
};

export default function Sidebar({
    activeTab,
    onTabChange,
    tabs,
    isOpen,
    onClose
}) {
    return (
        <>
            {/* Mobile overlay */}
            {isOpen && (
                <div
                    className="fixed inset-0 bg-black/50 z-40 lg:hidden"
                    onClick={onClose}
                />
            )}

            {/* Sidebar */}
            <aside
                className={cn(
                    'fixed top-0 left-0 h-full w-72 bg-white dark:bg-dark-card border-r border-gray-200 dark:border-dark-border z-50 transition-transform duration-300',
                    'lg:translate-x-0 lg:static',
                    isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
                )}
            >
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-dark-border">
                    <div className="flex items-center gap-2">
                        <Rocket className="w-8 h-8 text-primary-600" />
                        <h1 className="text-xl font-bold text-gray-900 dark:text-white">
                            {APP_NAME}
                        </h1>
                    </div>
                    <button
                        onClick={onClose}
                        className="lg:hidden p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg"
                    >
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* Navigation */}
                <nav className="p-4 space-y-2">
                    {tabs.map((tab) => {
                        const Icon = iconMap[tab.icon];
                        const isActive = activeTab === tab.id;

                        return (
                            <button
                                key={tab.id}
                                onClick={() => {
                                    onTabChange(tab.id);
                                    if (window.innerWidth < 1024) onClose();
                                }}
                                className={cn(
                                    'w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200',
                                    'hover:bg-gray-100 dark:hover:bg-gray-800',
                                    isActive
                                        ? 'bg-primary-50 dark:bg-primary-900/20 text-primary-600 dark:text-primary-400'
                                        : 'text-gray-700 dark:text-gray-300'
                                )}
                            >
                                <Icon className="w-5 h-5" />
                                <span className="font-medium">{tab.label}</span>
                            </button>
                        );
                    })}
                </nav>

                {/* Footer */}
                <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-200 dark:border-dark-border">
                    <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
                        v2.0.0 - Universidad Icesi
                    </p>
                </div>
            </aside>
        </>
    );
}

export function MobileMenuButton({ onClick }) {
    return (
        <button
            onClick={onClick}
            className="lg:hidden p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg"
        >
            <Menu className="w-6 h-6" />
        </button>
    );
}
