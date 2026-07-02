/*
 * PathBack — The Good Neighbor Guard
 * Built by Christopher Hughes · Sacramento, CA
 * Created with the help of AI collaborators (Claude · GPT · Gemini · Groq)
 * Truth · Safety · We Got Your Back
 */

import React, { useState, useEffect } from 'react';

// Sun-over-the-winding-path mark, drawn in code so the landing page has no
// image dependencies and ships inside the build.
const PathBackMark = ({ size = 52 }) => (
  <svg width={size} height={size} viewBox="0 0 64 64" aria-hidden="true">
    <circle cx="32" cy="32" r="29" fill="#0d2b23" stroke="#3e8e4f" strokeWidth="3.5" />
    <g fill="#ffb300">
      <circle cx="32" cy="24" r="8" />
      <g stroke="#ffb300" strokeWidth="2.5" strokeLinecap="round">
        <line x1="32" y1="10" x2="32" y2="14" />
        <line x1="20" y1="14" x2="22.5" y2="17.5" />
        <line x1="44" y1="14" x2="41.5" y2="17.5" />
        <line x1="15" y1="24" x2="19" y2="24" />
        <line x1="49" y1="24" x2="45" y2="24" />
      </g>
    </g>
    <path d="M3 40 Q16 30 30 37 T61 36 L61 56 Q32 66 3 56 Z" fill="#2e7d32" />
    <path d="M3 44 Q20 38 34 43 T61 42 L61 56 Q32 66 3 56 Z" fill="#1b5e20" />
    <path
      d="M30 61 C26 54 42 50 36 44 C32 40 36 37 40 36"
      fill="none" stroke="#fff3d6" strokeWidth="4.5" strokeLinecap="round"
    />
  </svg>
);

const LandingScreen = ({ onGetHelp, onUpgrade, hasPass }) => {
  const [version, setVersion] = useState('');

  useEffect(() => {
    fetch('/health')
      .then(res => res.json())
      .then(data => setVersion(data.version))
      .catch(() => setVersion(''));
  }, []);

  return (
    <div className="pb-landing">
      {/* ── HERO ── */}
      <header className="pb-hero">
        <div className="pb-logo-row">
          <PathBackMark />
          <div>
            <div className="pb-wordmark">PATH<span>BACK</span></div>
            <div className="pb-logo-tagline">— Get back on your path. —</div>
          </div>
        </div>

        <h1 className="pb-headline">
          When life knocks you off course,{' '}
          <span className="pb-headline-accent">PathBack</span> helps you find
          your next step.
        </h1>

        <div className="pb-mini-features">
          <span>🛡 Slow down.</span>
          <span className="pb-mini-divider" />
          <span>🧠 Think clearly.</span>
          <span className="pb-mini-divider" />
          <span>➜ Move forward.</span>
        </div>

        <p className="pb-hero-copy">
          Whether you're dealing with a difficult situation, writing an
          important message, or trying to figure out what to do next, PathBack
          helps you organize your thoughts, understand your options, and move
          forward with confidence.
        </p>
      </header>

      {/* ── ACTION CARDS ── */}
      <section className="pb-cards">
        <div className="pb-card pb-card-problem">
          <div className="pb-card-icon pb-card-icon-problem">📝</div>
          <h2>Handle a Problem</h2>
          <div className="pb-card-kicker pb-kicker-problem">
            When something has already happened.
          </div>
          <p>
            Landlord issues. Work problems. Debt collectors. Insurance
            questions. Scams. Difficult conversations.
          </p>
          <p>
            PathBack helps you organize what happened, draft a clear response,
            and think through practical next steps.
          </p>
          <button
            className="pb-card-btn pb-btn-problem"
            onClick={() => onGetHelp('protection')}
          >
            Handle a Problem <span aria-hidden="true">→</span>
          </button>
        </div>

        <div className="pb-card pb-card-think">
          <div className="pb-card-icon pb-card-icon-think">🧠</div>
          <h2>Think It Through</h2>
          <div className="pb-card-kicker pb-kicker-think">
            When you need perspective.
          </div>
          <p>
            Thought Partner doesn't tell you what to think. It helps you
            think.
          </p>
          <p>
            Ask difficult questions. Challenge your assumptions. Explore
            different perspectives. Work through decisions before you act.
          </p>
          <button
            className="pb-card-btn pb-btn-think"
            onClick={() => onGetHelp('thought')}
          >
            Think It Through <span aria-hidden="true">→</span>
          </button>
        </div>
      </section>

      {!hasPass && onUpgrade && (
        <div className="pb-upgrade-row">
          <button type="button" className="pb-upgrade-link" onClick={onUpgrade}>
            ⭐ Need more than the free tier? Go unlimited — from $6.99
          </button>
        </div>
      )}

      {/* ── PRINCIPLES ── */}
      <section className="pb-principles">
        <div className="pb-principles-title">
          <span className="pb-rule" />
          Built on The Good Neighbor Guard principles
          <span className="pb-rule" />
        </div>
        <div className="pb-principles-row">
          <div className="pb-principle"><span>✅</span>Truth over convenience</div>
          <div className="pb-principle"><span>🔒</span>Safety before shortcuts</div>
          <div className="pb-principle"><span>👤</span>Privacy respected</div>
          <div className="pb-principle"><span>🤝</span>We've Got Your Back</div>
        </div>
      </section>

      {/* ── FEATURE STRIP ── */}
      <section className="pb-feature-strip">
        <div className="pb-feature">
          <span className="pb-feature-icon">🎁</span>
          <div>
            <strong>Start Free</strong>
            <div>Three free responses every day.</div>
          </div>
        </div>
        <div className="pb-feature">
          <span className="pb-feature-icon">🌐</span>
          <div>
            <strong>Any Device</strong>
            <div>Works in any web browser.</div>
          </div>
        </div>
        <div className="pb-feature">
          <span className="pb-feature-icon">✅</span>
          <div>
            <strong>No Installation</strong>
            <div>No downloads. No hassle.</div>
          </div>
        </div>
        <div className="pb-feature">
          <span className="pb-feature-icon">🏠</span>
          <div>
            <strong>Built by</strong>
            <div>The Good Neighbor Guard</div>
          </div>
        </div>
      </section>

      {/* ── FOOTER ── */}
      <footer className="pb-footer">
        <div className="pb-footer-inner">
          <p className="pb-footer-disclaimer">
            PathBack provides information and drafting assistance to help you
            think through situations. It is not a law firm, attorney, financial
            advisor, therapist, or emergency service. When professional advice
            is needed, PathBack encourages you to contact a qualified
            professional.
          </p>
          <div className="pb-footer-brand">
            <div className="pb-footer-gng">THE GOOD NEIGHBOR GUARD</div>
            <div className="pb-footer-tagline">Truth · Safety · We've Got Your Back</div>
            {version && <div className="pb-footer-version">{version}</div>}
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingScreen;
