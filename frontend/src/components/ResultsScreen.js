/*
 * The Guard Table — The Good Neighbor Guard
 * Built by Christopher Hughes · Sacramento, CA
 * Created with the help of AI collaborators (Claude · GPT · Gemini · Groq)
 * Truth · Safety · We Got Your Back
 */

import React, { useState, useEffect } from 'react';

// FAQ data for each category
const FAQ_DATA = {
  housing: [
    "What if my landlord retaliates after I send this?",
    "What if I don't have a written lease?",
    "Can I be evicted for complaining?",
    "What if I can't afford a lawyer?"
  ],
  job: [
    "Can I get fired for reporting this?",
    "What if I don't have documentation?",
    "What if I'm undocumented — can I still file?",
    "How long do I have before the filing deadline?"
  ],
  money: [
    "What if the debt collector calls again after I send this?",
    "Can they garnish my wages?",
    "What if the debt isn't mine?",
    "Will this hurt my credit score?"
  ],
  benefits: [
    "What if I miss the appeal deadline?",
    "Can I get backdated benefits?",
    "What if I was never told about my right to appeal?",
    "What if I need help filling out the forms?"
  ],
  family: [
    "What if the contractor threatens me?",
    "What if I already paid them?",
    "How do I prove what happened?",
    "What if this person is a friend or family member?"
  ],
  other: [
    "What if they ignore my message?",
    "Can I get help if I can't afford a lawyer?",
    "What documentation should I keep?",
    "How long do I have to take action?"
  ]
};

const ResultsScreen = ({ results, category, onStartNew }) => {
  const [showWait, setShowWait] = useState(false);
  const [showLeverage, setShowLeverage] = useState(false);
  const [showGuard, setShowGuard] = useState(false);
  const [typingMessage, setTypingMessage] = useState('');
  const [copyButtonText, setCopyButtonText] = useState('Copy to clipboard');
  const [expandedFAQ, setExpandedFAQ] = useState({});

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

  const toggleFAQ = (index) => {
    setExpandedFAQ(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
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

        {/* PEOPLE ALSO ASK */}
        {showGuard && category && FAQ_DATA[category] && (
          <div className="faq-section" style={{
            marginTop: '32px',
            marginBottom: '32px'
          }}>
            <div style={{
              fontSize: '18px',
              fontWeight: 'bold',
              marginBottom: '16px',
              color: '#fff'
            }}>
              People Also Ask
            </div>
            {FAQ_DATA[category].map((question, index) => (
              <div key={index} style={{
                backgroundColor: '#1a1a1a',
                border: '1px solid #333',
                borderRadius: '8px',
                marginBottom: '8px',
                overflow: 'hidden'
              }}>
                <button
                  onClick={() => toggleFAQ(index)}
                  style={{
                    width: '100%',
                    padding: '12px 16px',
                    background: 'transparent',
                    border: 'none',
                    color: '#fff',
                    textAlign: 'left',
                    fontSize: '14px',
                    cursor: 'pointer',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                  }}
                >
                  <span>{question}</span>
                  <span style={{
                    transform: expandedFAQ[index] ? 'rotate(180deg)' : 'rotate(0deg)',
                    transition: 'transform 0.3s ease'
                  }}>
                    ▼
                  </span>
                </button>
                {expandedFAQ[index] && (
                  <div style={{
                    padding: '12px 16px',
                    borderTop: '1px solid #333',
                    backgroundColor: '#0a0a0a',
                    color: '#8899aa',
                    fontSize: '13px',
                    lineHeight: '1.4'
                  }}>
                    This is a common concern. Each situation is unique, so the specific steps may vary. The message above gives you the strongest legal foundation to start with. If you need personalized guidance, search "[your county] legal aid" for free local resources, or contact 211 for help finding assistance in your area.
                  </div>
                )}
              </div>
            ))}
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
            <div style={{
              backgroundColor: '#1a1a1a',
              border: '1px solid #333',
              borderRadius: '8px',
              padding: '12px',
              margin: '16px 0 8px 0',
              fontSize: '12px',
              color: '#8899aa',
              lineHeight: '1.4'
            }}>
              ⚠️ <strong>Important:</strong> The Guard Table uses AI to generate responses based on general legal patterns. Information provided may not reflect the most current laws or apply perfectly to your specific situation. Do not rely solely on this information for legal decisions. Free legal aid is available in most areas — search "[your county] legal aid" to find help near you. In an emergency, contact 211 for local resources.
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default ResultsScreen;