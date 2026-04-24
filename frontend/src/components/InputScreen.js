/*
 * The Guard Table — The Good Neighbor Guard
 * Built by Christopher Hughes · Sacramento, CA
 * Created with the help of AI collaborators (Claude · GPT · Gemini · Groq)
 * Truth · Safety · We Got Your Back
 */

import React, { useState } from 'react';

const InputScreen = ({ category, onSubmit, defaultState }) => {
  const [input, setInput] = useState('');
  const [state, setState] = useState(defaultState);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const categoryNames = {
    housing: 'My Housing',
    money: 'Money Issues',
    job: 'My Job',
    benefits: 'Benefits/Insurance',
    family: 'My Family',
    other: 'Something Else'
  };

  const states = [
    'Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California', 'Colorado', 'Connecticut',
    'Delaware', 'Florida', 'Georgia', 'Hawaii', 'Idaho', 'Illinois', 'Indiana', 'Iowa',
    'Kansas', 'Kentucky', 'Louisiana', 'Maine', 'Maryland', 'Massachusetts', 'Michigan',
    'Minnesota', 'Mississippi', 'Missouri', 'Montana', 'Nebraska', 'Nevada', 'New Hampshire',
    'New Jersey', 'New Mexico', 'New York', 'North Carolina', 'North Dakota', 'Ohio',
    'Oklahoma', 'Oregon', 'Pennsylvania', 'Rhode Island', 'South Carolina', 'South Dakota',
    'Tennessee', 'Texas', 'Utah', 'Vermont', 'Virginia', 'Washington', 'West Virginia',
    'Wisconsin', 'Wyoming'
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    setIsSubmitting(true);
    await onSubmit(input, state, []);
    setIsSubmitting(false);
  };

  const handleVoiceInput = () => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      const recognition = new SpeechRecognition();

      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'en-US';

      recognition.onresult = (event) => {
        let transcript = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
          if (event.results[i].isFinal) {
            transcript += event.results[i][0].transcript;
          }
        }
        setInput(prev => prev + transcript);
      };

      recognition.start();
    } else {
      alert('Voice recognition not supported in this browser');
    }
  };

  const handlePhotoUpload = (e) => {
    // Placeholder for photo upload functionality
    alert('Photo upload coming soon');
  };

  return (
    <div className="input-screen">
      <div className="input-header">
        <div className="input-category">{categoryNames[category] || category}</div>
      </div>

      <form className="input-form" onSubmit={handleSubmit}>
        <textarea
          className="input-textarea"
          placeholder="Tell me exactly what happened. Don't filter it. Don't calm it down. Just say it like you're telling your best friend."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          rows={8}
        />

        <div className="input-controls">
          <button
            type="button"
            className="input-btn"
            onClick={handleVoiceInput}
          >
            🎤 Voice input
          </button>
          <button
            type="button"
            className="input-btn"
            onClick={handlePhotoUpload}
          >
            📷 Photo upload
          </button>
        </div>

        <select
          className="state-select"
          value={state}
          onChange={(e) => setState(e.target.value)}
        >
          <option value="">What state are you in?</option>
          {states.map(stateName => (
            <option key={stateName} value={stateName}>{stateName}</option>
          ))}
        </select>

        <button
          type="submit"
          className="btn btn-primary"
          disabled={!input.trim() || !state || isSubmitting}
          style={{ alignSelf: 'center' }}
        >
          {isSubmitting ? 'Getting your response...' : 'Get my response'}
        </button>
      </form>
    </div>
  );
};

export default InputScreen;