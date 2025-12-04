/**
 * ThemeToggle Component
 */
import { Moon, Sun } from 'lucide-react';
import { useEffect } from 'react';
import useStore from '../../store';
import Button from './Button';

export default function ThemeToggle() {
    const { theme, toggleTheme } = useStore();

    useEffect(() => {
        if (theme === 'dark') {
            document.documentElement.classList.add('dark');
        } else {
            document.documentElement.classList.remove('dark');
        }
    }, [theme]);

    return (
        <Button
            variant="ghost"
            size="sm"
            onClick={toggleTheme}
            icon={theme === 'dark' ? Sun : Moon}
            aria-label="Toggle theme"
        >
            {theme === 'dark' ? 'Claro' : 'Oscuro'}
        </Button>
    );
}
