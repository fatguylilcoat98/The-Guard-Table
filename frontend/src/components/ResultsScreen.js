/*
 * The Guard Table — The Good Neighbor Guard
 * Built by Christopher Hughes · Sacramento, CA
 * Created with the help of AI collaborators (Claude · GPT · Gemini · Groq)
 * Truth · Safety · We Got Your Back
 */

import React, { useState, useEffect } from 'react';

const ResultsScreen = ({ results, onStartNew }) => {
  const [showWait, setShowWait] = useState(false);
  const [showLeverage, setShowLeverage] = useState(false);
  const [showGuard, setShowGuard] = useState(false);
  const [typingMessage, setTypingMessage] = useState('');
  const [copyButtonText, setCopyButtonText] = useState('Copy to clipboard');

  useEffect(() => {
    if (!results || results.error) return;

    // Two second pause, then show everything in sequence
    const timer1 = setTimeout(() => {
      setShowWait(true);
    }, 2000);

    const timer2 = setTimeout(() => {
      setShowLeverage(true);
      // Start typing animation for leverage message
      if (results.leverage) {
        typeMessage(results.leverage);
      }
    }, 4000);

    const timer3 = setTimeout(() => {
      setShowGuard(true);
    }, 6000);

    return () => {
      clearTimeout(timer1);
      clearTimeout(timer2);
      clearTimeout(timer3);
    };
  }, [results]);

  const typeMessage = (message) => {
    let i = 0;
    const speed = 30; // milliseconds per character
    const timer = setInterval(() => {
      setTypingMessage(message.slice(0, i));
      i++;
      if (i > message.length) {
        clearInterval(timer);
      }
    }, speed);
  };

  const handleCopy = async () => {
    if (results.leverage) {
      try {
        await navigator.clipboard.writeText(results.leverage);
        setCopyButtonText('✓ Copied');
        setTimeout(() => setCopyButtonText('Copy to clipboard'), 2000);
      } catch (err) {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = results.leverage;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        setCopyButtonText('✓ Copied');
        setTimeout(() => setCopyButtonText('Copy to clipboard'), 2000);
      }
    }
  };

  const handleShare = () => {
    if (navigator.share) {
      navigator.share({
        title: 'The Guard Table helped me fight back',
        text: 'I stood up for my rights using The Guard Table. Every company has a system. Now so do you.',
        url: window.location.origin
      });
    } else {
      // Fallback: copy link to clipboard
      navigator.clipboard.writeText(window.location.origin);
      alert('Link copied to clipboard!');
    }
  };

  if (!results) {
    return (
      <div className="results-screen">
        <div style={{
          background: '#0a0a0a',
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          {/* Two second pause - just dark screen */}
        </div>
      </div>
    );
  }

  if (results.error) {
    return (
      <div className="results-screen">
        <div className="error-message">
          {results.error}
        </div>
        <div className="results-actions">
          <button className="btn" onClick={onStartNew}>
            Try again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="results-screen">
      <div className="results-container">
        {/* WAIT BLOCK */}
        {showWait && (
          <div className="wait-block">
            <div className="wait-header">
              ⛔ WAIT.
            </div>
            {results.wait && results.wait.map((line, index) => (
              <div key={index} className="wait-line" style={{animationDelay: `${index * 0.4}s`}}>
                {line}
              </div>
            ))}
          </div>
        )}

        {/* LEVERAGE BLOCK */}
        {showLeverage && (
          <div className="leverage-block">
            <div className="leverage-header">
              Here's what you send. Right now.
            </div>
            <div className="leverage-message">
              {typingMessage}
            </div>
            <div className="leverage-actions">
              <button
                className={`copy-btn ${copyButtonText.includes('Copied') ? 'copied' : ''}`}
                onClick={handleCopy}
              >
                {copyButtonText}
              </button>
              <button className="adjust-btn">Make it stronger</button>
              <button className="adjust-btn">Make it softer</button>
            </div>
            <div className="send-note">
              Send this by email or text. Keep the receipt. Do not call.
            </div>
          </div>
        )}

        {/* GUARD BLOCK */}
        {showGuard && (
          <div className="guard-block">
            <div className="guard-header">
              If they ignore this.
            </div>
            {results.guard_steps && results.guard_steps.map((step, index) => (
              <div key={index} className="guard-step" style={{animationDelay: `${index * 0.6}s`}}>
                <strong>Step {index + 1}:</strong> {step}
              </div>
            ))}
            <div className="guard-final">
              You are not alone in this. The Guard Table has your back.
            </div>
          </div>
        )}

        {/* ACTIONS */}
        {showGuard && (
          <>
            <div className="results-actions">
              <button className="btn" onClick={onStartNew}>
                Start a new issue
              </button>
              <button className="btn btn-primary" onClick={handleShare}>
                Share this
              </button>
            </div>
            <div className="remaining-count">
              {results.remaining_responses === 0 ? (
                "You've used your 5 free responses this month. Need more help? Email us at thegoodneighborguard@gmail.com — we'll figure it out together."
              ) : (
                `${results.remaining_responses} free responses remaining this month`
              )}
            </div>
            <div className="results-footer">
              The Good Neighbor Guard — Truth · Safety · We Got Your Back
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default ResultsScreen;