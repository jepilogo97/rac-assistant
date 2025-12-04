/**
 * Main App Component
 */
import { useState, useEffect } from 'react';
import MainLayout from './components/layout/MainLayout';
import UploadPage from './pages/Upload';
import ProcessPage from './pages/Process';
import ClassifierPage from './pages/Classifier';
import SegmenterPage from './pages/Segmenter';
import TOBEPage from './pages/TOBE';
import KPIsPage from './pages/KPIs';

function App() {
  const [activeTab, setActiveTab] = useState('upload');

  // Listen for hash changes to enable navigation
  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.slice(1); // Remove the '#'
      if (hash) {
        setActiveTab(hash);
      }
    };

    // Set initial tab from hash
    handleHashChange();

    // Listen for hash changes
    window.addEventListener('hashchange', handleHashChange);

    return () => {
      window.removeEventListener('hashchange', handleHashChange);
    };
  }, []);

  // Handle tab change and update hash
  const handleTabChange = (tabId) => {
    setActiveTab(tabId);
    window.location.hash = `#${tabId}`;
  };

  const renderPage = () => {
    switch (activeTab) {
      case 'upload':
        return <UploadPage />;
      case 'process':
        return <ProcessPage />;
      case 'classifier':
        return <ClassifierPage />;
      case 'segmenter':
        return <SegmenterPage />;
      case 'tobe':
        return <TOBEPage />;
      case 'kpis':
        return <KPIsPage />;
      default:
        return <UploadPage />;
    }
  };

  return (
    <MainLayout activeTab={activeTab} onTabChange={handleTabChange}>
      {renderPage()}
    </MainLayout>
  );
}

export default App;
