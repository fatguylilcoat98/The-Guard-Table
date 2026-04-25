/*
 * The Guard Table — The Good Neighbor Guard
 * Built by Christopher Hughes · Sacramento, CA
 * Created with the help of AI collaborators (Claude · GPT · Gemini · Groq)
 * Truth · Safety · We Got Your Back
 */

import React, { useState, useEffect } from 'react';

const LandingScreen = ({ onGetHelp }) => {
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
        <h1>Every company has a system.</h1>
        {showSecondLine && (
          <h2>Now so do you.</h2>
        )}
        <p className="landing-subtitle">
          Tell us what happened. We'll do the rest.
        </p>
        <div className="landing-cta">
          <button
            className="btn btn-glow"
            onClick={onGetHelp}
          >
            I need help right now
          </button>
        </div>
      </div>
      <div className="landing-footer">
        The Guard Table — The Good Neighbor Guard
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