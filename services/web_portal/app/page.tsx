export default function Home() {
  return (
    <div className="hero">
      <section>
        <h1>Route intelligence for modern field operations.</h1>
        <p>
          Mentis Optimisation is a scheduling and routing API built for complex
          job planning. Submit requests, track jobs, and scale through
          deterministic solver profiles.
        </p>
        <div className="hero-actions">
          <a className="button primary" href="/docs">
            View API Docs
          </a>
          <a className="button secondary" href="/portal">
            Open Developer Portal
          </a>
        </div>
        <div className="metrics">
          <div className="metric">
            <div>Async Jobs</div>
            <strong>Queue + Worker</strong>
          </div>
          <div className="metric">
            <div>Free Tier</div>
            <strong>Node-based</strong>
          </div>
          <div className="metric">
            <div>Mapping</div>
            <strong>OSRM Ready</strong>
          </div>
        </div>
      </section>
      <section className="highlight-card">
        <h2>Phase 2 Focus</h2>
        <p>
          This portal will expose API keys, usage analytics, and billing
          readiness. We are shipping documentation and onboarding first.
        </p>
        <div className="gradient-panel">
          <h3>Developer Experience</h3>
          <p>
            Use the API today. Add your mapping server. Monitor jobs in real
            time. Integrate with your workforce tools without rework.
          </p>
        </div>
      </section>

      <section className="feature-grid">
        <div className="feature-card">
          <h3>Adaptive Routing</h3>
          <p>Multi-vehicle, multi-day solver tuned for real-world constraints.</p>
        </div>
        <div className="feature-card">
          <h3>Deterministic Runs</h3>
          <p>Pin random seeds and collect reproducible outputs.</p>
        </div>
        <div className="feature-card">
          <h3>Usage Guardrails</h3>
          <p>Enforce node-based caps and prepare for billing.</p>
        </div>
      </section>
    </div>
  );
}
