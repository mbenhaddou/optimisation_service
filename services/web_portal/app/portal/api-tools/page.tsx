export default function ApiToolsPage() {
  return (
    <div className="portal-page">
      <div className="portal-header">
        <div>
          <h1>API Tools</h1>
          <p className="portal-subtitle">
            Test `/v1/optimize`, `/v1/matrix`, and `/v1/reoptimize` requests.
          </p>
        </div>
        <div className="portal-header-actions">
          <a className="button primary" href="/portal/test">
            Open API Console
          </a>
        </div>
      </div>

      <div className="portal-grid-wide">
        <section className="portal-panel">
          <h3>Playground</h3>
          <p>
            The console lets you send optimization, matrix, and re-optimization
            requests with your API key and explore formatted JSON responses.
          </p>
          <div className="portal-placeholder">
            Use the console to validate requests before production integration.
          </div>
        </section>
        <section className="portal-panel">
          <h3>Request Templates</h3>
          <p>
            Save common payloads and reuse them across optimizations.
          </p>
          <div className="portal-placeholder">
            Templates will be stored with your workspace in Phase 3.
          </div>
        </section>
      </div>
    </div>
  );
}
