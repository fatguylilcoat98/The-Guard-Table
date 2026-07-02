/*
 * PathBack — The Good Neighbor Guard
 * Built by Christopher Hughes · Sacramento, CA
 * Created with the help of AI collaborators (Claude · GPT · Gemini · Groq)
 * Truth · Safety · We Got Your Back
 */

import React from 'react';

const CancelScreen = () => (
  <div style={{ padding: '48px 16px', maxWidth: '520px', margin: '0 auto', textAlign: 'center' }}>
    <h1 style={{ fontSize: '24px', marginBottom: '8px' }}>No charge — checkout canceled</h1>
    <p style={{ color: '#8899aa', lineHeight: 1.5 }}>
      You weren't charged anything. Your free responses are still here whenever
      you need them, and the upgrade will be waiting if you change your mind.
    </p>
    <button className="btn btn-primary" onClick={() => { window.location.href = '/'; }}>
      Back to PathBack
    </button>
    <div style={{ color: '#667788', fontSize: '11px', marginTop: '32px' }}>
      PathBack — Truth · Safety · We Got Your Back
    </div>
  </div>
);

export default CancelScreen;
