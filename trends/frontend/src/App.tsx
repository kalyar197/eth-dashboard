// src/App.tsx
/**
 * Main App component with three-tab navigation
 * Minimalist dark theme matching Dash dashboard
 */

import { useState } from 'react';
import { Management } from './components/Management';
import { WordCharts } from './components/WordCharts';
import { RegionCharts } from './components/RegionCharts';
import './index.css';

type Tab = 'management' | 'word-charts' | 'region-charts';

function App() {
  const [activeTab, setActiveTab] = useState<Tab>('management');

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Header */}
      <header className="border-b border-border">
        <div className="p-4">
          <h1 className="text-xl font-mono">Google Trends Data Collection</h1>
        </div>
      </header>

      {/* Tab Navigation */}
      <nav className="border-b border-border flex">
        <button
          className={`tab ${activeTab === 'management' ? 'tab-active' : ''}`}
          onClick={() => setActiveTab('management')}
        >
          Management
        </button>
        <button
          className={`tab ${activeTab === 'word-charts' ? 'tab-active' : ''}`}
          onClick={() => setActiveTab('word-charts')}
        >
          Word Charts
        </button>
        <button
          className={`tab ${activeTab === 'region-charts' ? 'tab-active' : ''}`}
          onClick={() => setActiveTab('region-charts')}
        >
          Region Charts
        </button>
      </nav>

      {/* Tab Content */}
      <main>
        {activeTab === 'management' && <Management />}
        {activeTab === 'word-charts' && <WordCharts />}
        {activeTab === 'region-charts' && <RegionCharts />}
      </main>
    </div>
  );
}

export default App;
