/*
 * The Guard Table — The Good Neighbor Guard
 * Built by Christopher Hughes · Sacramento, CA
 * Created with the help of AI collaborators (Claude · GPT · Gemini · Groq)
 * Truth · Safety · We Got Your Back
 */

import React from 'react';

const ModeSelectScreen = ({ onSelectMode }) => {
  const handleProtectionHelp = () => {
    onSelectMode('protection');
  };

  const handleThoughtPartner = () => {
    onSelectMode('thought');
  };

  return (
    <div className="mode-select-screen">
      <div className="mode-select-hero">
        <h1>How can we help you?</h1>
        <p className="mode-select-subtitle">
          Choose the type of support you need
        </p>
      </div>

      <div className="mode-options">
        <div className="mode-card protection-mode" onClick={handleProtectionHelp}>
          <div className="mode-icon">🛡️</div>
          <h2>Protection Guidance</h2>
          <p>
            Something happened to you. Get immediate guidance,
            scam protection, and actionable next steps.
          </p>
          <div className="mode-examples">
            <span>Scams</span>
            <span>Fraud</span>
            <span>Safety Issues</span>
            <span>Consumer Protection</span>
          </div>
          <button className="mode-button protection-button">
            I need protection
          </button>
        </div>

        <div className="mode-card thought-mode" onClick={handleThoughtPartner}>
          <div className="mode-icon">🧠</div>
          <h2>Thought Partner</h2>
          <p>
            Facing a big decision or complex problem? Get perspective,
            explore options, and think through what matters most.
          </p>
          <div className="mode-examples">
            <span>Career Decisions</span>
            <span>Life Changes</span>
            <span>Relationships</span>
            <span>Personal Growth</span>
          </div>
          <button className="mode-button thought-button">
            I need perspective
          </button>
        </div>
      </div>

      <div className="mode-footer">
        <p>Both modes remember your conversations and provide thoughtful, human-centered guidance.</p>
      </div>
    </div>
  );
};

export default ModeSelectScreen;