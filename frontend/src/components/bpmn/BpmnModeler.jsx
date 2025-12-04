/**
 * BPMN Modeler Component
 * Allows interactive editing of BPMN diagrams using bpmn-js Modeler
 */
import { useEffect, useRef } from 'react';
import BpmnModeler from 'bpmn-js/lib/Modeler';
import { ZoomIn, ZoomOut, Maximize2 } from 'lucide-react';
import 'bpmn-js/dist/assets/diagram-js.css';
import 'bpmn-js/dist/assets/bpmn-font/css/bpmn-embedded.css';

export default function BpmnModelerComponent({ xml, height = '500px', onXmlChange }) {
    const containerRef = useRef(null);
    const modelerRef = useRef(null);

    useEffect(() => {
        if (!containerRef.current) return;

        // Create modeler instance
        if (!modelerRef.current) {
            modelerRef.current = new BpmnModeler({
                container: containerRef.current,
                keyboard: {
                    bindTo: document
                }
            });

            // Listen to changes
            if (onXmlChange) {
                const modeler = modelerRef.current;
                const eventBus = modeler.get('eventBus');

                // Debounce XML export
                let timeout;
                const handleChange = () => {
                    clearTimeout(timeout);
                    timeout = setTimeout(async () => {
                        try {
                            const { xml: newXml } = await modeler.saveXML({ format: true });
                            onXmlChange(newXml);
                        } catch (err) {
                            console.error('Error exporting XML:', err);
                        }
                    }, 500);
                };

                // Listen to various change events
                eventBus.on('commandStack.changed', handleChange);
                eventBus.on('shape.added', handleChange);
                eventBus.on('shape.removed', handleChange);
                eventBus.on('connection.added', handleChange);
                eventBus.on('connection.removed', handleChange);
                eventBus.on('elements.changed', handleChange);
            }
        }

        const modeler = modelerRef.current;

        // Load and display diagram
        if (xml) {
            modeler.importXML(xml)
                .then(({ warnings }) => {
                    if (warnings.length) {
                        console.warn('BPMN import warnings:', warnings);
                    }

                    // Fit diagram to viewport with proper centering
                    const canvas = modeler.get('canvas');
                    canvas.zoom('fit-viewport', 'auto');

                    // Enable mouse wheel zoom
                    const zoomScroll = modeler.get('zoomScroll');
                    if (zoomScroll) {
                        zoomScroll._enabled = true;
                    }
                })
                .catch((err) => {
                    console.error('Error importing BPMN:', err);
                });
        }

        // Cleanup
        return () => {
            if (modelerRef.current) {
                modelerRef.current.destroy();
                modelerRef.current = null;
            }
        };
    }, [xml]);

    const handleZoomIn = () => {
        if (modelerRef.current) {
            const canvas = modelerRef.current.get('canvas');
            const viewbox = canvas.viewbox();
            const currentZoom = viewbox.scale;
            const newZoom = currentZoom * 1.2; // Increase by 20%

            // Get center of current viewport
            const centerX = viewbox.x + viewbox.width / 2;
            const centerY = viewbox.y + viewbox.height / 2;

            canvas.zoom(newZoom, { x: centerX, y: centerY });
        }
    };

    const handleZoomOut = () => {
        if (modelerRef.current) {
            const canvas = modelerRef.current.get('canvas');
            const viewbox = canvas.viewbox();
            const currentZoom = viewbox.scale;
            const newZoom = currentZoom * 0.8; // Decrease by 20%

            // Get center of current viewport
            const centerX = viewbox.x + viewbox.width / 2;
            const centerY = viewbox.y + viewbox.height / 2;

            canvas.zoom(newZoom, { x: centerX, y: centerY });
        }
    };

    const handleZoomReset = () => {
        if (modelerRef.current) {
            const canvas = modelerRef.current.get('canvas');
            canvas.zoom('fit-viewport');
        }
    };

    return (
        <div style={{ position: 'relative', height, width: '100%' }}>
            <div
                ref={containerRef}
                style={{
                    height: '100%',
                    width: '100%',
                    border: '1px solid #e5e7eb',
                    borderRadius: '0.5rem',
                    cursor: 'grab'
                }}
                className="bg-white dark:bg-gray-800"
            />

            {/* Zoom Controls */}
            <div className="absolute top-4 right-4 flex flex-col gap-2 z-10">
                <button
                    onClick={handleZoomIn}
                    className="p-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg shadow-md hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                    title="Zoom In (+)"
                >
                    <ZoomIn className="w-5 h-5 text-gray-700 dark:text-gray-300" />
                </button>
                <button
                    onClick={handleZoomOut}
                    className="p-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg shadow-md hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                    title="Zoom Out (-)"
                >
                    <ZoomOut className="w-5 h-5 text-gray-700 dark:text-gray-300" />
                </button>
                <button
                    onClick={handleZoomReset}
                    className="p-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg shadow-md hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                    title="Ajustar al tamaño (F)"
                >
                    <Maximize2 className="w-5 h-5 text-gray-700 dark:text-gray-300" />
                </button>
            </div>
        </div>
    );
}
