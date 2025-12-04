/**
 * Header Component
 */
import { Settings } from 'lucide-react';
import { useState } from 'react';
import useStore from '../../store';
import Button from '../common/Button';
import ThemeToggle from '../common/ThemeToggle';
import { MobileMenuButton } from './Sidebar';
import SettingsModal from './SettingsModal';

export default function Header({ onMenuClick }) {
    const { apiKey } = useStore();
    const [isSettingsOpen, setIsSettingsOpen] = useState(false);

    return (
        <>
            <header className="bg-white dark:bg-dark-card border-b border-gray-200 dark:border-dark-border px-6 py-4">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <MobileMenuButton onClick={onMenuClick} />
                        <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                            Optimización Inteligente de Procesos
                        </h2>
                    </div>

                    <div className="flex items-center gap-3">
                        {/* Settings Button */}
                        <Button
                            variant={apiKey ? 'outline' : 'primary'}
                            size="sm"
                            icon={Settings}
                            onClick={() => setIsSettingsOpen(true)}
                            className={!apiKey ? "animate-pulse" : ""}
                        >
                            {apiKey ? 'Configuración' : 'Configurar Proyecto'}
                        </Button>

                        {/* Theme Toggle */}
                        <ThemeToggle />
                    </div>
                </div>
            </header>

            <SettingsModal
                isOpen={isSettingsOpen}
                onClose={() => setIsSettingsOpen(false)}
            />
        </>
    );
}
