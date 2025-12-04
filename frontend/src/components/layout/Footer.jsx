/**
 * Footer Component
 */
export default function Footer() {
    return (
        <footer className="bg-white dark:bg-dark-card border-t border-gray-200 dark:border-dark-border px-6 py-4 mt-auto">
            <div className="flex flex-col md:flex-row items-center justify-between gap-4">
                <p className="text-sm text-gray-600 dark:text-gray-400">
                    © 2025 RAC Assistant - Universidad Icesi
                </p>
                <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
                    <a href="#" className="hover:text-primary-600 transition-colors">
                        Documentación
                    </a>
                    <span>•</span>
                    <a href="#" className="hover:text-primary-600 transition-colors">
                        Soporte
                    </a>
                    <span>•</span>
                    <a
                        href="https://github.com/jepilogo97/rac-assistant"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="hover:text-primary-600 transition-colors"
                    >
                        GitHub
                    </a>
                </div>
            </div>
        </footer>
    );
}
