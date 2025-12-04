/**
 * BPMN CSS Imports
 * Import BPMN.js styles globally
 */
import 'bpmn-js/dist/assets/diagram-js.css';
import 'bpmn-js/dist/assets/bpmn-font/css/bpmn-embedded.css';

// Additional custom styles for BPMN viewer
const style = document.createElement('style');
style.textContent = `
  .bjs-container {
    background-color: #fafafa;
  }
  
  .dark .bjs-container {
    background-color: #1f2937;
  }
  
  .bjs-powered-by {
    display: none !important;
  }
`;
document.head.appendChild(style);
