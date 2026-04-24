/*
 * The Guard Table — The Good Neighbor Guard
 * Built by Christopher Hughes · Sacramento, CA
 * Created with the help of AI collaborators (Claude · GPT · Gemini · Groq)
 * Truth · Safety · We Got Your Back
 */

import React, { useState } from 'react';
import './App.css';
import LandingScreen from './components/LandingScreen';
import CategoryScreen from './components/CategoryScreen';
import InputScreen from './components/InputScreen';
import ResultsScreen from './components/ResultsScreen';

function App() {
  const [currentScreen, setCurrentScreen] = useState('landing');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [userState, setUserState] = useState('California');
  const [currentInput, setCurrentInput] = useState('');
  const [results, setResults] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [adminToken, setAdminToken] = useState(localStorage.getItem('guardTableAdminToken') || '');
  const [adminPanelCollapsed, setAdminPanelCollapsed] = useState(!!localStorage.getItem('guardTableAdminToken'));

  const handleGetHelp = () => {
    setCurrentScreen('category');
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
      {/* Admin Status Box */}
      {adminToken && (
        <div style={{
          position: 'fixed',
          top: '10px',
          left: '50%',
          transform: 'translateX(-50%)',
          backgroundColor: '#FFD700',
          color: '#000',
          padding: '4px 12px',
          fontSize: '12px',
          fontWeight: 'bold',
          borderRadius: '4px',
          zIndex: 10000,
          boxShadow: '0 2px 8px rgba(0,0,0,0.3)'
        }}>
          admin access
        </div>
      )}

      <div>
        {renderScreen()}
      </div>

      {/* Admin Panel */}
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
    </div>
  );
}

export default App;
