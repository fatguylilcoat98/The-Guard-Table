/*
 * The Guard Table — The Good Neighbor Guard
 * Built by Christopher Hughes · Sacramento, CA
 * Created with the help of AI collaborators (Claude · GPT · Gemini · Groq)
 * Truth · Safety · We Got Your Back
 */

import React, { useState, useEffect } from 'react';
import './App.css';
import LandingScreen from './components/LandingScreen';
import ModeSelectScreen from './components/ModeSelectScreen';
import CategoryScreen from './components/CategoryScreen';
import InputScreen from './components/InputScreen';
import ResultsScreen from './components/ResultsScreen';
import ThoughtPartnerScreen from './components/ThoughtPartnerScreen';

function App() {
  const [currentScreen, setCurrentScreen] = useState('landing');
  const [selectedMode, setSelectedMode] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [userState, setUserState] = useState('California');
  const [currentInput, setCurrentInput] = useState('');
  const [results, setResults] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [adminToken, setAdminToken] = useState(localStorage.getItem('guardTableAdminToken') || '');
  const [adminPanelCollapsed, setAdminPanelCollapsed] = useState(!!localStorage.getItem('guardTableAdminToken'));
  const [showAdminPanel, setShowAdminPanel] = useState(false);

  // Show admin panel with Ctrl+Shift+A combination
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.ctrlKey && e.shiftKey && e.key === 'A') {
        e.preventDefault();
        setShowAdminPanel(true);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const handleGetHelp = () => {
    setCurrentScreen('mode-select');
  };

  const handleModeSelect = (mode) => {
    setSelectedMode(mode);
    if (mode === 'protection') {
      setCurrentScreen('category');
    } else if (mode === 'thought') {
      setCurrentScreen('thought-partner');
    }
  };

  const handleCategorySelect = (category) => {
    setSelectedCategory(category);
    setCurrentScreen('input');
  };

  const handleSubmitInput = async (input, state, photos) => {
    setUserState(state);
    setCurrentInput(input);
    setIsLoading(true);
    setCurrentScreen('results');

    // Call the backend API
    try {
      const response = await fetch('/api/guard', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          category: selectedCategory,
          state: state,
          rant: input,
          ...(adminToken && { admin_token: adminToken })
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setResults(data);
      } else {
        setResults({
          error: "Something went wrong — try again"
        });
      }
    } catch (error) {
      setResults({
        error: "Something went wrong — try again"
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleStartNew = () => {
    setCurrentScreen('landing');
    setSelectedMode('');
    setSelectedCategory('');
    setCurrentInput('');
    setResults(null);
  };

  const handleBackToInput = () => {
    setCurrentScreen('input');
    setResults(null);
  };

  const handleBackToCategory = () => {
    setCurrentScreen('category');
    setCurrentInput('');
  };

  const handleAdminTokenChange = (token) => {
    setAdminToken(token);
    if (token) {
      localStorage.setItem('guardTableAdminToken', token);
    } else {
      localStorage.removeItem('guardTableAdminToken');
      setAdminPanelCollapsed(false);
    }
  };

  const handleAdminTokenSubmit = () => {
    if (adminToken.trim()) {
      setAdminPanelCollapsed(true);
    }
  };

  const handleAdminPanelClick = () => {
    if (adminPanelCollapsed) {
      setAdminToken('');
      localStorage.removeItem('guardTableAdminToken');
      setAdminPanelCollapsed(false);
    }
  };

  const renderScreen = () => {
    switch (currentScreen) {
      case 'landing':
        return <LandingScreen onGetHelp={handleGetHelp} />;
      case 'mode-select':
        return <ModeSelectScreen onSelectMode={handleModeSelect} />;
      case 'thought-partner':
        return <ThoughtPartnerScreen
          onBack={() => setCurrentScreen('mode-select')}
          onStartNew={handleStartNew}
        />;
      case 'category':
        return <CategoryScreen onSelectCategory={handleCategorySelect} />;
      case 'input':
        return <InputScreen
          category={selectedCategory}
          onSubmit={handleSubmitInput}
          defaultState={userState}
          defaultInput={currentInput}
          onBack={handleBackToCategory}
        />;
      case 'results':
        return <ResultsScreen
          results={results}
          category={selectedCategory}
          isLoading={isLoading}
          adminToken={adminToken}
          onStartNew={handleStartNew}
          onBack={handleBackToInput}
        />;
      default:
        return <LandingScreen onGetHelp={handleGetHelp} />;
    }
  };

  return (
    <div className="App">
      {/* Admin Status Text - Only show when admin panel is visible */}
      {adminToken && showAdminPanel && (
        <div style={{
          position: 'fixed',
          top: '10px',
          right: '10px',
          color: '#FFD700',
          fontSize: '12px',
          fontWeight: 'bold',
          zIndex: 10000
        }}>
          admin access
        </div>
      )}

      <div>
        {renderScreen()}
      </div>

      {/* Admin Panel - Hidden by default, Ctrl+Shift+A to show */}
      {showAdminPanel && (
        <div style={{
        position: 'fixed',
        bottom: '10px',
        right: '10px',
        backgroundColor: '#1a1a1a',
        border: '1px solid #333',
        borderRadius: adminPanelCollapsed ? '50%' : '8px',
        padding: adminPanelCollapsed ? '8px' : '8px 12px',
        fontSize: '12px',
        color: '#8899aa',
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        zIndex: 1000,
        cursor: adminPanelCollapsed ? 'pointer' : 'default',
        transition: 'all 0.3s ease',
        width: adminPanelCollapsed ? '32px' : 'auto',
        height: adminPanelCollapsed ? '32px' : 'auto',
        justifyContent: 'center'
      }}
      onClick={handleAdminPanelClick}
      title={adminPanelCollapsed ? 'Click to remove admin access' : 'Enter admin token'}
      >
        {adminPanelCollapsed ? (
          <span style={{ color: '#00ff00', fontSize: '14px' }}>⚡</span>
        ) : (
          <>
            <span>Admin:</span>
            <input
              type="password"
              placeholder="Token"
              value={adminToken}
              onChange={(e) => handleAdminTokenChange(e.target.value)}
              onBlur={handleAdminTokenSubmit}
              onKeyDown={(e) => e.key === 'Enter' && handleAdminTokenSubmit()}
              style={{
                background: '#000',
                border: '1px solid #333',
                borderRadius: '4px',
                padding: '4px 8px',
                color: '#fff',
                fontSize: '12px',
                width: '100px'
              }}
              onClick={(e) => e.stopPropagation()}
            />
          </>
        )}
      </div>
      )}
    </div>
  );
}

export default App;
