/*
 * PathBack — The Good Neighbor Guard
 * Built by Christopher Hughes · Sacramento, CA
 * Created with the help of AI collaborators (Claude · GPT · Gemini · Groq)
 * Truth · Safety · We Got Your Back
 */

import React, { useState, useEffect, useRef } from 'react';

// After Stripe redirects back, the webhook may still be in flight —
// poll the backend briefly until the access pass shows up.
const MAX_ATTEMPTS = 10;
const POLL_INTERVAL_MS = 2000;

const SuccessScreen = ({ onAccessToken }) => {
  const [status, setStatus] = useState('loading'); // loading | ready | timeout | missing
  const [pass, setPass] = useState(null);
  const [copied, setCopied] = useState(false);
  const attempts = useRef(0);

  useEffect(() => {
    const sessionId = new URLSearchParams(window.location.search).get('session_id');
    if (!sessionId) {
      setStatus('missing');
      return;
    }

    let cancelled = false;
    const poll = async () => {
      attempts.current += 1;
      try {
        const response = await fetch(`/api/stripe/session-pass?session_id=${encodeURIComponent(sessionId)}`);
        if (response.status === 200) {
          const data = await response.json();
          if (!cancelled && data.ready) {
            setPass(data);
            setStatus('ready');
            localStorage.setItem('pathbackAccessToken', data.token);
            if (onAccessToken) onAccessToken(data.token);
            return;
          }
        }
      } catch (e) {
        // transient — keep polling
      }
      if (!cancelled) {
        if (attempts.current >= MAX_ATTEMPTS) {
          setStatus('timeout');
        } else {
          setTimeout(poll, POLL_INTERVAL_MS);
        }
      }
    };
    poll();
    return () => { cancelled = true; };
  }, [onAccessToken]);

  const copyToken = async () => {
    try {
      await navigator.clipboard.writeText(pass.token);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (e) { /* clipboard unavailable */ }
  };

  const passLabel = pass && pass.pass_type === 'pass_7day'
    ? '7-Day Pass'
    : pass && pass.pass_type === 'sub_yearly' ? 'Yearly Subscription' : 'Monthly Subscription';

  return (
    <div style={{ padding: '48px 16px', maxWidth: '520px', margin: '0 auto', textAlign: 'center' }}>
      {status === 'loading' && (
        <>
          <h1 style={{ fontSize: '24px' }}>Finishing up…</h1>
          <p style={{ color: '#8899aa' }}>Confirming your payment with Stripe. This usually takes a few seconds.</p>
        </>
      )}

      {status === 'ready' && pass && (
        <>
          <h1 style={{ fontSize: '26px', marginBottom: '8px' }}>✅ You're in.</h1>
          <p style={{ color: '#8899aa', lineHeight: 1.5 }}>
            Your {passLabel} is active. This device is already unlocked —
            and here's your access code in case you need it on another device:
          </p>
          <div style={{
            backgroundColor: '#1a1a1a', border: '1px solid #333', borderRadius: '8px',
            padding: '16px', margin: '16px 0', fontFamily: 'monospace', fontSize: '15px',
            wordBreak: 'break-all', color: '#fff'
          }}>
            {pass.token}
          </div>
          <button className="btn" onClick={copyToken} style={{ marginBottom: '12px' }}>
            {copied ? '✓ Copied' : 'Copy access code'}
          </button>
          <div>
            <button className="btn btn-primary" onClick={() => { window.location.href = '/'; }}>
              Start using PathBack
            </button>
          </div>
          {pass.expires_at && (
            <p style={{ color: '#667788', fontSize: '12px', marginTop: '16px' }}>
              Active through {new Date(pass.expires_at).toLocaleDateString()}
            </p>
          )}
        </>
      )}

      {status === 'timeout' && (
        <>
          <h1 style={{ fontSize: '24px' }}>Payment received — pass on its way</h1>
          <p style={{ color: '#8899aa', lineHeight: 1.5 }}>
            Stripe confirmed your payment but our system hasn't issued your pass yet.
            Refresh this page in a minute. If it still doesn't appear, email
            thegoodneighborguard@gmail.com with your receipt and we'll sort it out fast.
          </p>
          <button className="btn" onClick={() => window.location.reload()}>Refresh</button>
        </>
      )}

      {status === 'missing' && (
        <>
          <h1 style={{ fontSize: '24px' }}>Hmm — no checkout session found</h1>
          <p style={{ color: '#8899aa' }}>
            This page only works right after a Stripe checkout.
          </p>
          <button className="btn btn-primary" onClick={() => { window.location.href = '/'; }}>
            Back to PathBack
          </button>
        </>
      )}

      <div style={{ color: '#667788', fontSize: '11px', marginTop: '32px' }}>
        PathBack — Truth · Safety · We Got Your Back
      </div>
    </div>
  );
};

export default SuccessScreen;
