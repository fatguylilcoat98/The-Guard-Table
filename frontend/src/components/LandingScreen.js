/*
 * PathBack — The Good Neighbor Guard
 * Built by Christopher Hughes · Sacramento, CA
 * Created with the help of AI collaborators (Claude · GPT · Gemini · Groq)
 * Truth · Safety · We Got Your Back
 */

import React, { useState, useEffect } from 'react';

const LandingScreen = ({ onGetHelp, onUpgrade, hasPass }) => {
  const [showSecondLine, setShowSecondLine] = useState(false);
  const [version, setVersion] = useState('');

  useEffect(() => {
    // Show the second line after a pause
    const timer = setTimeout(() => {
      setShowSecondLine(true);
    }, 1500);

    // Fetch version info
    fetch('/health')
      .then(res => res.json())
      .then(data => setVersion(data.version))
      .catch(() => setVersion(''));

    return () => clearTimeout(timer);
  }, []);

  return (
    <div className="landing-screen">
      <div className="landing-hero">
        <h1>PathBack</h1>
        {showSecondLine && (
          <h2>Get back on your path.</h2>
        )}
        <p className="landing-subtitle">
          When someone knocks you off course, PathBack helps you stand your
          ground and get back on your path.
        </p>
        <div className="landing-cta">
          <button
            className="btn btn-protection"
            onClick={() => onGetHelp('protection')}
          >
            🛡️ I need protection
          </button>
          <button
            className="btn btn-thought"
            onClick={() => onGetHelp('thought')}
          >
            🧠 I need perspective
          </button>
        </div>
        {onUpgrade && !hasPass && (
          <button
            type="button"
            onClick={onUpgrade}
            style={{
              background: 'transparent',
              border: '1px solid #333',
              borderRadius: '6px',
              color: '#8899aa',
              fontSize: '13px',
              padding: '8px 16px',
              marginTop: '16px',
              cursor: 'pointer'
            }}
          >
            ⭐ Go unlimited — from $6.99
          </button>
        )}
      </div>
      <div className="landing-footer">
        PathBack — The Good Neighbor Guard · Truth · Safety · We Got Your Back
        {version && (
          <div style={{
            fontSize: '10px',
            color: '#666',
            marginTop: '4px',
            fontFamily: 'monospace'
          }}>
            {version}
          </div>
        )}
      </div>
    </div>
  );
};

export default LandingScreen;
