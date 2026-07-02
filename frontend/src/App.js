/*
 * PathBack — The Good Neighbor Guard
 * Built by Christopher Hughes · Sacramento, CA
 * Created with the help of AI collaborators (Claude · GPT · Gemini · Groq)
 * Truth · Safety · We Got Your Back
 */

import React, { useState, useEffect } from 'react';
import './App.css';
import LandingScreen from './components/LandingScreen';
import CategoryScreen from './components/CategoryScreen';
import InputScreen from './components/InputScreen';
import ResultsScreen from './components/ResultsScreen';
import ThoughtPartnerScreen from './components/ThoughtPartnerScreen';
import UpgradeScreen from './components/UpgradeScreen';
import SuccessScreen from './components/SuccessScreen';
import CancelScreen from './components/CancelScreen';
import { streamGuardResponse, parseGuardSections } from './guardStream';

function initialScreen() {
  if (window.location.pathname === '/success') return 'success';
  if (window.location.pathname === '/cancel') return 'cancel';
  return 'landing';
}

function App() {
  const [currentScreen, setCurrentScreen] = useState(initialScreen());
  const [selectedCategory, setSelectedCategory] = useState('');
  const [userState, setUserState] = useState('California');
  const [currentInput, setCurrentInput] = useState('');
  const [results, setResults] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [adminToken, setAdminToken] = useState(localStorage.getItem('guardTableAdminToken') || '');
  const [accessToken, setAccessToken] = useState(localStorage.getItem('pathbackAccessToken') || '');
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

  // Allow setting the admin token via URL (?admin_token=...) so it can be
  // enabled on mobile where Ctrl+Shift+A isn't available. The token is
  // stored in localStorage and stripped from the URL so it isn't left in
  // browser history or shared by accident.
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const urlToken = params.get('admin_token');
    if (urlToken) {
      setAdminToken(urlToken);
      localStorage.setItem('guardTableAdminToken', urlToken);
      setAdminPanelCollapsed(true);
      params.delete('admin_token');
      const clean = window.location.pathname + (params.toString() ? '?' + params.toString() : '');
      window.history.replaceState({}, '', clean);
    }
  }, []);

  const handleGetHelp = (mode) => {
    if (mode === 'protection') {
      setCurrentScreen('category');
    } else if (mode === 'thought') {
      setCurrentScreen('thought-partner');
    }
  };


  const handleSwitchMode = (mode) => {
    setSelectedCategory(''); // Reset category when switching modes
    setCurrentInput(''); // Reset input when switching modes
    setResults(null); // Reset results when switching modes
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

  const handleUpgrade = () => {
    setCurrentScreen('upgrade');
  };

  const authFields = () => ({
    ...(adminToken && { admin_token: adminToken }),
    ...(accessToken && { access_token: accessToken }),
  });

  const handleSubmitInput = async (input, state, photos) => {
    setUserState(state);
    setCurrentInput(input);
    setIsLoading(true);
    setResults(null);
    setCurrentScreen('results');

    let buffer = '';
    let notice = '';
    let disclaimer = '';
    try {
      await streamGuardResponse({
        body: {
          category: selectedCategory,
          state,
          rant: input,
          ...authFields(),
        },
        onEvent: (evt) => {
          if (evt.type === 'meta') {
            disclaimer = evt.disclaimer || '';
          } else if (evt.type === 'notice') {
            notice = evt.message || '';
          } else if (evt.type === 'text') {
            buffer += evt.chunk;
            const parsed = parseGuardSections(buffer);
            if (parsed.wait.length || parsed.leverage || parsed.guard_steps.length) {
              setIsLoading(false);
              setResults({
                wait: parsed.wait,
                leverage: parsed.leverage,
                guard_steps: parsed.guard_steps,
                notice,
                streaming: true,
              });
            }
          } else if (evt.type === 'done') {
            const parsed = parseGuardSections(buffer);
            const leverage = evt.citation_warning
              ? `${parsed.leverage}\n\nNote: ${evt.citation_warning}`
              : parsed.leverage;
            setIsLoading(false);
            setResults({
              wait: parsed.wait,
              leverage,
              guard_steps: parsed.guard_steps,
              plan: evt.plan,
              remaining_responses: evt.remaining_responses,
              version: evt.version,
              served_by: evt.served_by,
              downgraded: evt.downgraded,
              disclaimer: evt.disclaimer || disclaimer,
              notice,
              streaming: false,
            });
          } else if (evt.type === 'error') {
            setIsLoading(false);
            setResults({ error: evt.message || 'Something went wrong — try again' });
          }
        },
        onHttpError: (status, errBody) => {
          setIsLoading(false);
          const msg = (errBody && errBody.message) || 'Something went wrong — try again';
          setResults({ error: msg, canUpgrade: status === 429 });
        },
      });
    } catch (error) {
      setIsLoading(false);
      setResults({ error: 'Something went wrong — try again' });
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
        return <LandingScreen onGetHelp={handleGetHelp} onUpgrade={handleUpgrade} hasPass={!!accessToken} />;
      case 'thought-partner':
        return <ThoughtPartnerScreen
          onBack={() => setCurrentScreen('landing')}
          onStartNew={handleStartNew}
          onSwitchMode={handleSwitchMode}
          accessToken={accessToken}
          adminToken={adminToken}
        />;
      case 'category':
        return <CategoryScreen
          onSelectCategory={handleCategorySelect}
          onSwitchMode={handleSwitchMode}
        />;
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
          onUpgrade={handleUpgrade}
        />;
      case 'upgrade':
        return <UpgradeScreen onBack={handleStartNew} />;
      case 'success':
        return <SuccessScreen onAccessToken={setAccessToken} />;
      case 'cancel':
        return <CancelScreen />;
      default:
        return <LandingScreen onGetHelp={handleGetHelp} onUpgrade={handleUpgrade} hasPass={!!accessToken} />;
    }
  };

  return (
    <div className="App">
      {/* Admin Status Text - visible whenever an admin token is active
          (works on mobile, where the Ctrl+Shift+A panel isn't reachable) */}
      {adminToken && (
        <div style={{
          position: 'fixed',
          top: '10px',
          right: '10px',
          color: '#00ff88',
          background: 'rgba(0,0,0,0.6)',
          padding: '4px 8px',
          borderRadius: '6px',
          fontSize: '12px',
          fontWeight: 'bold',
          zIndex: 10000
        }}>
          ⚡ unlimited
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
