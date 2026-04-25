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

const ResultsScreen = ({ results, category, isLoading, adminToken, onStartNew, onBack }) => {
  const [showWait, setShowWait] = useState(false);
  const [showLeverage, setShowLeverage] = useState(false);
  const [showGuard, setShowGuard] = useState(false);
  const [typingMessage, setTypingMessage] = useState('');
  const [copyButtonText, setCopyButtonText] = useState('Copy to clipboard');
  const [expandedFAQ, setExpandedFAQ] = useState({});
  const [adjustingTone, setAdjustingTone] = useState('');
  const [adjustedLeverage, setAdjustedLeverage] = useState('');
  const [loadingText, setLoadingText] = useState('Reading your situation...');
  const [showFollowUp, setShowFollowUp] = useState(false);
  const [followUpText, setFollowUpText] = useState('');

  useEffect(() => {
    // Loading text cycling
    if (isLoading) {
      const loadingMessages = [
        'Reading your situation...',
        'Finding the right law...',
        'Building your response...'
      ];
      let index = 0;
      const interval = setInterval(() => {
        index = (index + 1) % loadingMessages.length;
        setLoadingText(loadingMessages[index]);
      }, 2000);
      return () => clearInterval(interval);
    }
  }, [isLoading]);

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
    const textToCopy = adjustedLeverage || results.leverage;
    if (textToCopy) {
      try {
        await navigator.clipboard.writeText(textToCopy);
        setCopyButtonText('✓ Copied');
        setTimeout(() => setCopyButtonText('Copy to clipboard'), 2000);
      } catch (err) {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = textToCopy;
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

  const adjustTone = async (direction) => {
    if (!results?.leverage) return;

    setAdjustingTone(direction);

    try {
      const instruction = direction === 'stronger'
        ? 'Rewrite this message with more direct, firm language. More assertive.'
        : 'Rewrite this message with more professional, measured language. Less confrontational.';

      const response = await fetch('/api/guard', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          category: category,
          state: 'California', // Use stored state if available
          rant: `${instruction}\n\nOriginal message:\n${results.leverage}`,
          ...(adminToken && { admin_token: adminToken })
        }),
      });

      if (response.ok) {
        const data = await response.json();
        if (data.leverage) {
          setAdjustedLeverage(data.leverage);
        }
      }
    } catch (error) {
      console.error('Tone adjustment failed:', error);
    } finally {
      setAdjustingTone('');
    }
  };

  // Paid tier features (only visible with admin token)
  const downloadPDF = () => {
    const content = `
THE GUARD TABLE RESPONSE

WAIT:
${results.wait ? results.wait.join('\n') : ''}

LEVERAGE MESSAGE:
${adjustedLeverage || results.leverage || ''}

GUARD STEPS:
${results.guard_steps ? results.guard_steps.map((step, i) => `${i + 1}. ${step}`).join('\n') : ''}

Generated by The Guard Table
Truth · Safety · We Got Your Back
    `.trim();

    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'guard-table-response.txt';
    a.click();
    URL.revokeObjectURL(url);
  };

  const saveResponse = () => {
    const responseData = {
      category,
      timestamp: new Date().toISOString(),
      wait: results.wait,
      leverage: adjustedLeverage || results.leverage,
      guard_steps: results.guard_steps
    };

    const saved = JSON.parse(localStorage.getItem('guardTableSaved') || '[]');
    saved.push(responseData);
    localStorage.setItem('guardTableSaved', JSON.stringify(saved));

    alert('Response saved to your session');
  };

  const handleFollowUp = async () => {
    if (!followUpText.trim()) return;

    // This would make an API call for follow-up without counting against limits
    // For now, just show an alert
    alert(`Follow-up feature coming soon!\nYour question: "${followUpText}"`);
    setShowFollowUp(false);
    setFollowUpText('');
  };

  if (isLoading || !results) {
    return (
      <div className="results-screen">
        <div style={{
          background: '#0a0a0a',
          minHeight: '100vh',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          position: 'relative'
        }}>
          {onBack && (
            <button
              onClick={onBack}
              style={{
                position: 'absolute',
                top: '20px',
                left: '20px',
                background: 'transparent',
                border: 'none',
                color: '#8899aa',
                fontSize: '14px',
                cursor: 'pointer'
              }}
            >
              ← Back
            </button>
          )}
          {isLoading && (
            <div style={{
              fontSize: '18px',
              color: '#0066ff',
              fontWeight: 'bold',
              animation: 'pulse 1.5s infinite'
            }}>
              {loadingText}
            </div>
          )}
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
      {onBack && (
        <button
          onClick={onBack}
          style={{
            position: 'absolute',
            top: '20px',
            left: '20px',
            background: 'transparent',
            border: 'none',
            color: '#8899aa',
            fontSize: '14px',
            cursor: 'pointer',
            zIndex: 1000
          }}
        >
          ← Back
        </button>
      )}
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
            <div className="leverage-message" style={{
              fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
              fontSize: '14px',
              lineHeight: '1.5',
              letterSpacing: 'normal',
              maxWidth: '100%',
              wordWrap: 'break-word',
              padding: '16px',
              backgroundColor: '#1a1a1a',
              border: '1px solid #333',
              borderRadius: '8px',
              margin: '16px 0',
              whiteSpace: 'pre-wrap'
            }}>
              {adjustedLeverage || typingMessage}
            </div>
            <div className="leverage-actions" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <button
                className={`copy-btn ${copyButtonText.includes('Copied') ? 'copied' : ''}`}
                onClick={handleCopy}
                style={{
                  fontSize: '16px',
                  fontWeight: 'bold',
                  padding: '12px 24px',
                  backgroundColor: '#0066ff',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  width: '100%'
                }}
              >
                {copyButtonText}
              </button>
              <div style={{ display: 'flex', gap: '8px' }}>
                <button
                  className="adjust-btn"
                  onClick={() => adjustTone('stronger')}
                  disabled={adjustingTone !== ''}
                  style={{
                    fontSize: '12px',
                    padding: '6px 12px',
                    backgroundColor: 'transparent',
                    color: '#8899aa',
                    border: '1px solid #333',
                    borderRadius: '4px',
                    cursor: adjustingTone === '' ? 'pointer' : 'not-allowed',
                    flex: 1
                  }}
                >
                  {adjustingTone === 'stronger' ? 'Adjusting...' : 'Make it stronger'}
                </button>
                <button
                  className="adjust-btn"
                  onClick={() => adjustTone('softer')}
                  disabled={adjustingTone !== ''}
                  style={{
                    fontSize: '12px',
                    padding: '6px 12px',
                    backgroundColor: 'transparent',
                    color: '#8899aa',
                    border: '1px solid #333',
                    borderRadius: '4px',
                    cursor: adjustingTone === '' ? 'pointer' : 'not-allowed',
                    flex: 1
                  }}
                >
                  {adjustingTone === 'softer' ? 'Adjusting...' : 'Make it softer'}
                </button>
              </div>
            </div>
            <div className="send-note">
              {(() => {
                if (category === 'job') return 'Send this by text or email. Keep screenshots and pay records. Don\'t handle it only by phone.';
                if (category === 'housing') return 'Send this by text or email. Keep screenshots, photos, rent receipts, and any notices. Don\'t handle it only by phone.';
                if (category === 'money') return 'Send this in writing. Keep copies of every message, letter, and call log.';
                return 'Send this by text or email. Keep screenshots. Don\'t call.';
              })()}
            </div>

            {/* PAID TIER FEATURES - Only visible with admin token */}
            {adminToken && (
              <div style={{
                marginTop: '20px',
                padding: '16px',
                border: '2px solid #FFD700',
                borderRadius: '8px',
                backgroundColor: 'rgba(255, 215, 0, 0.1)'
              }}>
                <div style={{
                  fontSize: '14px',
                  color: '#FFD700',
                  fontWeight: 'bold',
                  marginBottom: '12px'
                }}>
                  🔥 PAID TIER FEATURES (Testing Mode)
                </div>
                <div style={{
                  display: 'flex',
                  gap: '8px',
                  flexWrap: 'wrap'
                }}>
                  <button
                    onClick={downloadPDF}
                    style={{
                      background: '#FFD700',
                      color: '#000',
                      border: 'none',
                      borderRadius: '4px',
                      padding: '8px 16px',
                      fontSize: '12px',
                      fontWeight: 'bold',
                      cursor: 'pointer'
                    }}
                  >
                    📄 Download PDF
                  </button>
                  <button
                    onClick={() => setShowFollowUp(!showFollowUp)}
                    style={{
                      background: '#FFD700',
                      color: '#000',
                      border: 'none',
                      borderRadius: '4px',
                      padding: '8px 16px',
                      fontSize: '12px',
                      fontWeight: 'bold',
                      cursor: 'pointer'
                    }}
                  >
                    💬 Follow-up Question
                  </button>
                  <button
                    onClick={saveResponse}
                    style={{
                      background: '#FFD700',
                      color: '#000',
                      border: 'none',
                      borderRadius: '4px',
                      padding: '8px 16px',
                      fontSize: '12px',
                      fontWeight: 'bold',
                      cursor: 'pointer'
                    }}
                  >
                    💾 Save Response
                  </button>
                </div>
                {showFollowUp && (
                  <div style={{
                    marginTop: '12px',
                    padding: '12px',
                    backgroundColor: 'rgba(0, 0, 0, 0.3)',
                    borderRadius: '4px'
                  }}>
                    <textarea
                      placeholder="Ask a follow-up question about this situation..."
                      value={followUpText}
                      onChange={(e) => setFollowUpText(e.target.value)}
                      style={{
                        width: '100%',
                        minHeight: '60px',
                        padding: '8px',
                        background: '#000',
                        border: '1px solid #333',
                        borderRadius: '4px',
                        color: '#fff',
                        fontSize: '14px',
                        resize: 'vertical'
                      }}
                    />
                    <div style={{ marginTop: '8px', display: 'flex', gap: '8px' }}>
                      <button
                        onClick={handleFollowUp}
                        disabled={!followUpText.trim()}
                        style={{
                          background: followUpText.trim() ? '#FFD700' : '#666',
                          color: '#000',
                          border: 'none',
                          borderRadius: '4px',
                          padding: '6px 12px',
                          fontSize: '12px',
                          cursor: followUpText.trim() ? 'pointer' : 'not-allowed'
                        }}
                      >
                        Ask Follow-up
                      </button>
                      <button
                        onClick={() => setShowFollowUp(false)}
                        style={{
                          background: 'transparent',
                          color: '#8899aa',
                          border: '1px solid #333',
                          borderRadius: '4px',
                          padding: '6px 12px',
                          fontSize: '12px',
                          cursor: 'pointer'
                        }}
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}
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
              {(() => {
                if (category === 'housing') return 'Don\'t leave voluntarily because of a threat. Start with the message above.';
                if (category === 'job') return 'Don\'t let this stay verbal. Start with the message above.';
                if (category === 'money') return 'Don\'t pay until they prove the debt. Start with the message above.';
                if (category === 'other') {
                  // Check if it's likely a scam based on common keywords
                  const leverageText = (results.leverage || '').toLowerCase();
                  if (leverageText.includes('deposit') || leverageText.includes('zelle') || leverageText.includes('venmo') || leverageText.includes('cash app')) {
                    return 'Don\'t send the money. Start with the message above.';
                  }
                }
                return 'Start with the message above.';
              })()}
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