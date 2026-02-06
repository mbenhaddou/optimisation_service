const apiBase = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export default function PortalPage() {
  return (
    <div className="page-card">
      <h1>Developer Portal</h1>
      <p>
        This is the foundation for user onboarding, API keys, and usage
        analytics. We will connect it to the API in Phase 3.
      </p>
      <div className="feature-grid">
        <div className="feature-card">
          <h3>API Keys</h3>
          <p>Admins can create keys via {apiBase}/v1/admin/api-keys.</p>
        </div>
        <div className="feature-card">
          <h3>Usage Analytics</h3>
          <p>Monthly usage is tracked by node-count matrix units.</p>
        </div>
        <div className="feature-card">
          <h3>Billing Ready</h3>
          <p>Stripe integration is planned for Phase 4.</p>
        </div>
      </div>

      <div className="hero-actions" style={{ marginTop: "32px" }}>
        <a className="button primary" href="/portal/test">
          Open API Test Console
        </a>
      </div>
    </div>
  );
}
