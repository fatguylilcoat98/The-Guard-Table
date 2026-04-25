/*
 * The Guard Table — The Good Neighbor Guard
 * Built by Christopher Hughes · Sacramento, CA
 * Created with the help of AI collaborators (Claude · GPT · Gemini · Groq)
 * Truth · Safety · We Got Your Back
 */

import React, { useState, useEffect, useRef } from 'react';

const ThoughtPartnerScreen = ({ onBack, onStartNew }) => {
  const [messages, setMessages] = useState([
    {
      type: 'assistant',
      content: "I'm here to think alongside you. What's on your mind? Whether it's a decision you're facing, a problem you're working through, or just something you want to explore - I'm curious to hear your perspective.",
      timestamp: new Date()
    }
  ]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!inputText.trim() || isLoading) return;

    const userMessage = {
      type: 'user',
      content: inputText.trim(),
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setIsLoading(true);

    try {
      const response = await fetch('/api/thought-partner', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: inputText.trim(),
          conversation_history: messages
        }),
      });

      if (response.ok) {
        const data = await response.json();
        const assistantMessage = {
          type: 'assistant',
          content: data.response,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, assistantMessage]);
      } else {
        throw new Error('Failed to get response');
      }
    } catch (error) {
      const errorMessage = {
        type: 'assistant',
        content: "I'm having trouble connecting right now. Could you try rephrasing your thought?",
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const formatTime = (timestamp) => {
    return timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="thought-partner-screen">
      <div className="tp-header">
        <button className="tp-back-btn" onClick={onBack}>
          ←
        </button>
        <div className="tp-title">
          <h2>🧠 Thought Partner</h2>
          <p>Let's think through this together</p>
        </div>
        <button className="tp-new-btn" onClick={onStartNew}>
          New
        </button>
      </div>

      <div className="tp-conversation">
        {messages.map((message, index) => (
          <div key={index} className={`tp-message ${message.type}`}>
            <div className="tp-message-content">
              <div className="tp-message-text">{message.content}</div>
              <div className="tp-message-time">{formatTime(message.timestamp)}</div>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="tp-message assistant">
            <div className="tp-message-content">
              <div className="tp-thinking">
                <div className="tp-thinking-dots">
                  <span>•</span>
                  <span>•</span>
                  <span>•</span>
                </div>
                <div className="tp-thinking-text">Thinking with you...</div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="tp-input-section">
        <div className="tp-input-group">
          <textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Share what's on your mind... I'm here to explore it with you."
            className="tp-input"
            disabled={isLoading}
            rows="3"
          />
          <button
            onClick={handleSend}
            disabled={!inputText.trim() || isLoading}
            className="tp-send-btn"
          >
            💭
          </button>
        </div>
        <div className="tp-input-hint">
          Press Enter to send, Shift+Enter for new line
        </div>
      </div>
    </div>
  );
};

export default ThoughtPartnerScreen;