/*
 * PathBack — The Good Neighbor Guard
 * Built by Christopher Hughes · Sacramento, CA
 * Created with the help of AI collaborators (Claude · GPT · Gemini · Groq)
 * Truth · Safety · We Got Your Back
 */

import React, { useState } from 'react';

const PRODUCTS = [
  {
    key: 'pass_7day',
    title: '7-Day Pass',
    price: '$6.99',
    cadence: 'one-time',
    blurb: 'Unlimited responses for 7 days. Perfect for getting through one fight.',
  },
  {
    key: 'sub_monthly',
    title: 'Monthly',
    price: '$11.99',
    cadence: 'per month',
    blurb: 'Unlimited responses, month to month. Cancel anytime.',
  },
  {
    key: 'sub_yearly',
    title: 'Yearly',
    price: '$99',
    cadence: 'per year',
    blurb: 'Unlimited responses all year. Two months free vs monthly.',
  },
];

const UpgradeScreen = ({ onBack }) => {
  const [loadingProduct, setLoadingProduct] = useState('');
  const [error, setError] = useState('');

  const startCheckout = async (product) => {
    setLoadingProduct(product);
    setError('');
    try {
      const response = await fetch('/api/stripe/create-checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ product }),
      });
      const data = await response.json();
      if (response.ok && data.url) {
        window.location.href = data.url;
      } else {
        setError(data.error || 'Checkout is unavailable right now — please try again shortly.');
        setLoadingProduct('');
      }
    } catch (e) {
      setError('Checkout is unavailable right now — please try again shortly.');
      setLoadingProduct('');
    }
  };

  return (
    <div className="upgrade-screen" style={{ padding: '24px 16px', maxWidth: '520px', margin: '0 auto' }}>
      {onBack && (
        <button
          type="button"
          onClick={onBack}
          style={{ background: 'transparent', border: 'none', color: '#8899aa', fontSize: '14px', cursor: 'pointer', marginBottom: '16px' }}
        >
          ← Back
        </button>
      )}
      <h1 style={{ fontSize: '26px', marginBottom: '8px' }}>Keep PathBack in your corner</h1>
      <p style={{ color: '#8899aa', marginBottom: '24px', lineHeight: 1.5 }}>
        Free users get 3 responses a day. Upgrade for unlimited responses,
        served by our strongest model.
      </p>

      {PRODUCTS.map((product) => (
        <div
          key={product.key}
          style={{
            backgroundColor: '#1a1a1a',
            border: '1px solid #333',
            borderRadius: '8px',
            padding: '16px',
            marginBottom: '12px',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
            <div style={{ fontSize: '18px', fontWeight: 'bold' }}>{product.title}</div>
            <div>
              <span style={{ fontSize: '20px', fontWeight: 'bold', color: '#0066ff' }}>{product.price}</span>
              <span style={{ fontSize: '12px', color: '#8899aa', marginLeft: '6px' }}>{product.cadence}</span>
            </div>
          </div>
          <p style={{ color: '#8899aa', fontSize: '13px', margin: '8px 0 12px 0', lineHeight: 1.4 }}>
            {product.blurb}
          </p>
          <button
            className="btn btn-primary"
            onClick={() => startCheckout(product.key)}
            disabled={loadingProduct !== ''}
            style={{ width: '100%', padding: '10px', fontSize: '15px' }}
          >
            {loadingProduct === product.key ? 'Opening checkout…' : `Get ${product.title}`}
          </button>
        </div>
      ))}

      {error && (
        <div style={{ color: '#ff6b6b', fontSize: '13px', marginTop: '8px' }}>{error}</div>
      )}

      <p style={{ color: '#667788', fontSize: '11px', marginTop: '20px', lineHeight: 1.5 }}>
        Payments are handled securely by Stripe. After checkout you'll receive an
        access code — keep it safe, it's your key to unlimited responses.
        PathBack — Truth · Safety · We Got Your Back.
      </p>
    </div>
  );
};

export default UpgradeScreen;
