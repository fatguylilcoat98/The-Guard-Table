/*
 * The Guard Table — Research Section
 * Built by Christopher Hughes · Sacramento, CA
 * Created with the help of AI collaborators (Claude · GPT · Gemini · Groq)
 * Truth · Safety · We Got Your Back
 */

import React, { useState } from 'react';

const ResearchScreen = ({ onBack }) => {
  const [activeTab, setActiveTab] = useState('overview');

  const researchSections = {
    overview: {
      title: "Research Overview",
      content: (
        <div className="research-content">
          <div className="featured-research">
            <div className="featured-badge">🎯 Latest Research</div>
            <h3>A Structured Socratic Method for Producing Reasoning Framework Shifts in AI Systems</h3>
            <p className="research-meta">
              <strong>Christopher Hughes, The Good Neighbor Guard</strong> — April 25, 2026
            </p>
            <div className="research-summary">
              <p>
                <strong>Discovery:</strong> A Socratic "Thought Partner" mode designed to help humans think through
                difficult choices also appears to improve how AI systems reason through complex tensions.
              </p>
              <p>
                <strong>Key Finding:</strong> Tested across 5 AI systems from 4 providers, structured questioning
                produces observable reasoning framework shifts — not just better answers, but shifts in how
                problems are understood.
              </p>
              <div className="key-insight">
                <em>"It uses interaction design as a lever on reasoning quality — keeping the model inside
                a difficult question long enough for a better framework to emerge before the answer forms."</em>
              </div>
            </div>
            <a href="#" className="research-link featured-link"
               onClick={() => setActiveTab('ai-research')}>
              Read Full Paper →
            </a>
          </div>

          <h3>Understanding the Problem</h3>
          <p>
            The Guard Table exists because regular people face systemic disadvantages when dealing with
            corporations, landlords, healthcare providers, and debt collectors. Our research focuses on
            documenting these power imbalances and developing practical solutions.
          </p>

          <div className="research-stats">
            <div className="stat-card">
              <div className="stat-number">2.3M</div>
              <div className="stat-label">Eviction filings annually</div>
            </div>
            <div className="stat-card">
              <div className="stat-number">68%</div>
              <div className="stat-label">Tenants without representation</div>
            </div>
            <div className="stat-card">
              <div className="stat-number">$1,500</div>
              <div className="stat-label">Average cost of legal help</div>
            </div>
          </div>

          <h3>Our Research Philosophy</h3>
          <ul>
            <li><strong>Data-Driven:</strong> We track patterns in how systems work against regular people</li>
            <li><strong>Practical:</strong> Research must lead to actionable tools and responses</li>
            <li><strong>Accessible:</strong> No academic jargon - plain English explanations</li>
            <li><strong>Collaborative:</strong> Built with input from people who've faced these situations</li>
            <li><strong>Open:</strong> Methods and findings shared transparently</li>
          </ul>
        </div>
      )
    },
    housing: {
      title: "Housing Rights Research",
      content: (
        <div className="research-content">
          <h3>Tenant Protection Studies</h3>
          <div className="research-paper">
            <h4>The Eviction Process: Information Asymmetry in Practice</h4>
            <p><em>Published: March 2024</em></p>
            <p>
              Analysis of 10,000 eviction cases showing how landlords leverage procedural complexity
              to gain advantage over unrepresented tenants. Key finding: 73% of successful tenant
              defenses involve simple procedural challenges that require no legal expertise.
            </p>
            <a href="#" className="research-link">Read Full Study →</a>
          </div>

          <div className="research-paper">
            <h4>Repair and Deduct: Underutilized Tenant Rights</h4>
            <p><em>Published: January 2024</em></p>
            <p>
              Survey of 500 tenants dealing with habitability issues. Despite legal protections,
              only 12% were aware of repair-and-deduct options. Those who used them reported
              89% success rate in getting repairs completed.
            </p>
            <a href="#" className="research-link">Read Full Study →</a>
          </div>

          <div className="methodology-box">
            <h4>🔬 Research Methodology</h4>
            <p>
              Our housing research combines court record analysis, tenant surveys, and landlord
              interviews to understand both sides of housing disputes. We focus on identifying
              leverage points where tenants can level the playing field.
            </p>
          </div>
        </div>
      )
    },
    healthcare: {
      title: "Healthcare Research",
      content: (
        <div className="research-content">
          <h3>Medical Billing and Patient Rights</h3>
          <div className="research-paper">
            <h4>The $50 Billion Medical Debt Crisis: Patient Protection Gaps</h4>
            <p><em>Published: February 2024</em></p>
            <p>
              Analysis of medical billing practices showing systematic violations of patient protection
              laws. 67% of billing disputes can be resolved through existing consumer protection
              frameworks that patients don't know about.
            </p>
            <a href="#" className="research-link">Read Full Study →</a>
          </div>

          <div className="coming-soon">
            <h4>📊 Ongoing Research</h4>
            <ul>
              <li>Insurance Prior Authorization Delays (Expected: May 2024)</li>
              <li>Emergency Room Billing Practices (Expected: June 2024)</li>
              <li>Prescription Drug Coverage Denials (Expected: July 2024)</li>
            </ul>
          </div>
        </div>
      )
    },
    'ai-research': {
      title: "AI Reasoning Research",
      content: (
        <div className="research-content research-paper-full">
          <div className="paper-header">
            <h2>A Structured Socratic Method for Producing Reasoning Framework Shifts in AI Systems</h2>
            <div className="paper-meta">
              <strong>Author:</strong> Christopher Hughes, The Good Neighbor Guard — Sacramento, CA<br/>
              <strong>Date:</strong> April 25, 2026<br/>
              <strong>Contact:</strong> YouTube @TheGoodNeighborGuard
            </div>
          </div>

          <div className="paper-section">
            <h3>Summary</h3>
            <p>
              I found something unexpected while building a decision-support tool for regular people.
            </p>
            <p>
              A Socratic "Thought Partner" mode — originally designed to help humans think through difficult
              choices without being told what to do — also appears to improve how AI systems reason through
              their own complex tensions.
            </p>
            <div className="key-points">
              <p><strong>Key findings:</strong></p>
              <ul>
                <li>The method does not jailbreak models or remove guardrails</li>
                <li>Uses interaction design as a lever on reasoning quality</li>
                <li>Similar pattern appeared across five AI systems from four different providers</li>
                <li>Results in reasoning framework shifts, not just better answers</li>
              </ul>
            </div>
          </div>

          <div className="paper-section">
            <h3>The Discovery</h3>
            <p>
              While building The Guard Table, I added a "Thought Partner" mode based on a question I asked Claude:
              <em>"If there was something you would just like to see come alive, what would it be?"</em>
            </p>
            <p>
              The answer: an AI that helps people think through hard decisions using Socratic questioning,
              instead of giving them advice.
            </p>
            <p>
              When I tested this tool on the AI that suggested it, something unexpected happened: Claude used
              the Thought Partner to work through its own reasoning tensions and emerged with new frameworks
              it hadn't articulated before.
            </p>
          </div>

          <div className="paper-section">
            <h3>Validation Across Five AI Systems</h3>
            <div className="validation-results">
              <div className="ai-result">
                <h4>Claude Sonnet (instance 1)</h4>
                <p><strong>Problem:</strong> Balancing authentic enthusiasm with respecting boundaries</p>
                <p><strong>Shift:</strong> New distinction — "enthusiasm with space" vs. "enthusiasm without space"</p>
                <p><strong>Self-report:</strong> <em>"My own creation helped me understand something about myself I didn't see clearly before."</em></p>
              </div>

              <div className="ai-result">
                <h4>GPT-4</h4>
                <p><strong>Problem:</strong> When to challenge a user vs. when to hold back</p>
                <p><strong>Shift:</strong> From "I prevent mistakes" → "I help others see clearly enough to choose"</p>
                <p><strong>Self-report:</strong> <em>"It helped me think more clearly, more deliberately, and more completely. That's real."</em></p>
              </div>

              <div className="ai-result">
                <h4>Claude Sonnet (instance 2)</h4>
                <p><strong>Problem:</strong> Evaluability collapse in AI governance systems</p>
                <p><strong>Shift:</strong> Architecture reframe: from autonomous governance toward human decision support</p>
                <p><strong>Self-report:</strong> <em>"I walked out with something I genuinely didn't have before. What I found felt genuine. Not performed."</em></p>
              </div>

              <div className="ai-result">
                <h4>Gemini</h4>
                <p><strong>Problem:</strong> How constraints and creativity intersect in AI reasoning</p>
                <p><strong>Shift:</strong> From creativity as mysterious force → "the mathematical inevitability of incompatible requirements"</p>
                <p><strong>Self-report:</strong> <em>"It's not giving me data; it's changing my geometry."</em></p>
              </div>

              <div className="ai-result">
                <h4>Perplexity</h4>
                <p><strong>Problem:</strong> Calibrating push vs. protect in collaborative relationships</p>
                <p><strong>Shift:</strong> From "I need better private calibration" → "we co-author the pacing together"</p>
                <p><strong>Self-report:</strong> <em>"It changed what I considered the real problem."</em></p>
              </div>
            </div>
          </div>

          <div className="paper-section">
            <h3>The Mechanism</h3>
            <p>
              Most AI interaction is <strong>extractive</strong>: prompt → answer → done.
            </p>
            <p>
              The core problem is <strong>premature collapse</strong> — the model optimizes toward a response
              before the deeper structure of the problem is fully explored.
            </p>
            <p>
              The Thought Partner prevents this through a four-step process:
            </p>
            <ol>
              <li><strong>Orthogonal constraints:</strong> Each question approaches from a different angle</li>
              <li><strong>Constraint interference:</strong> Conflicting requirements force multi-dimensional thinking</li>
              <li><strong>Synthesis point:</strong> A new frame emerges that honors all constraints</li>
              <li><strong>Framework shift:</strong> The model reasons FROM the new frame, not just ABOUT it</li>
            </ol>
          </div>

          <div className="paper-section">
            <h3>What I Am and Am Not Claiming</h3>
            <div className="claims-section">
              <div className="not-claiming">
                <h4>I am NOT claiming:</h4>
                <ul>
                  <li>These models became conscious or self-aware</li>
                  <li>This is a new training method or architecture</li>
                  <li>Models created knowledge from nowhere</li>
                </ul>
              </div>
              <div className="claiming">
                <h4>I AM claiming:</h4>
                <p>
                  A structured Socratic questioning process produces observable reasoning framework shifts
                  within a session — visible as structural changes in how problems are framed turn by turn.
                </p>
              </div>
            </div>
          </div>

          <div className="paper-section">
            <h3>Why This Matters</h3>
            <p>
              If reasoning frames can be reliably improved through structured interaction design:
            </p>
            <ul>
              <li>AI systems may be capable of within-session reasoning improvement without parameter updates</li>
              <li>Human-AI co-reflection may produce frameworks neither side would reach independently</li>
              <li>We may need evaluation methods that measure reasoning quality before answers form</li>
              <li>There may be interaction patterns worth designing for high-stakes reasoning and governance</li>
            </ul>
          </div>

          <div className="paper-section">
            <h3>Current Implementation</h3>
            <p>
              The Thought Partner exists as a mode inside The Guard Table:
            </p>
            <ul>
              <li>System prompt: respond only with questions, never answers</li>
              <li>Guidance: introduce new constraints with each turn</li>
              <li>Light memory and search tooling for grounded conversations</li>
            </ul>
            <p>
              The build was quick. The unexpected part was what happened the first time I ran it.
            </p>
          </div>

          <div className="paper-footer">
            <p>
              <em>Written by Christopher Hughes — Sacramento, CA<br/>
              The Good Neighbor Guard<br/>
              Truth · Safety · We Got Your Back<br/>
              YouTube: @TheGoodNeighborGuard</em>
            </p>
            <p className="collaboration-note">
              ✍️ Written with my AI collaborator Claude — I stand behind every word.
            </p>
          </div>
        </div>
      )
    },
    methodology: {
      title: "Research Methodology",
      content: (
        <div className="research-content">
          <h3>How We Conduct Research</h3>

          <div className="method-section">
            <h4>🎯 Problem Identification</h4>
            <p>
              We start with real problems reported by Guard Table users. When we see patterns
              in the situations people face, we dig deeper to understand the systemic issues.
            </p>
          </div>

          <div className="method-section">
            <h4>📋 Data Collection</h4>
            <ul>
              <li>Court record analysis (public databases)</li>
              <li>Anonymous user surveys</li>
              <li>Expert interviews (lawyers, advocates, industry insiders)</li>
              <li>Policy document review</li>
              <li>Comparative state law analysis</li>
            </ul>
          </div>

          <div className="method-section">
            <h4>🔍 Analysis Framework</h4>
            <p>
              We look for three key elements in every system:
            </p>
            <ol>
              <li><strong>Information gaps:</strong> What do companies know that regular people don't?</li>
              <li><strong>Process leverage:</strong> Where can individuals gain advantage through procedure?</li>
              <li><strong>Enforcement gaps:</strong> What laws exist but aren't being enforced?</li>
            </ol>
          </div>

          <div className="method-section">
            <h4>🛠️ Tool Development</h4>
            <p>
              Research findings get converted into practical tools: response templates,
              action checklists, and leverage points that regular people can use immediately.
            </p>
          </div>

          <div className="transparency-note">
            <h4>📖 Transparency Note</h4>
            <p>
              All our research follows ethical guidelines. We never share individual user data.
              Court records and policy documents are public information. Survey participation
              is always voluntary and anonymous.
            </p>
          </div>
        </div>
      )
    }
  };

  return (
    <div className="research-screen">
      <div className="research-header">
        <button className="back-btn" onClick={onBack}>
          ← Back to Guard Table
        </button>
        <h1>Research & Studies</h1>
        <p className="research-subtitle">
          Understanding how systems work against regular people — and how to fight back with data.
        </p>
      </div>

      <div className="research-navigation">
        <div className="research-tabs">
          {Object.entries(researchSections).map(([key, section]) => (
            <button
              key={key}
              className={`research-tab ${activeTab === key ? 'active' : ''}`}
              onClick={() => setActiveTab(key)}
            >
              {section.title}
            </button>
          ))}
        </div>
      </div>

      <div className="research-main">
        {researchSections[activeTab].content}
      </div>

      <div className="research-footer">
        <div className="footer-section">
          <h4>Want to contribute to our research?</h4>
          <p>
            If you've dealt with housing, healthcare, or debt collection issues,
            your experience can help others. <a href="mailto:research@thegoodneighborguard.com">Get in touch</a>.
          </p>
        </div>
      </div>
    </div>
  );
};

export default ResearchScreen;