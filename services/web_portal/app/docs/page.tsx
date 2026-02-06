const apiBase = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export default function DocsPage() {
  return (
    <div className="page-card">
      <h1>API Documentation</h1>
      <p>
        The API is documented via OpenAPI and served directly by the FastAPI
        service.
      </p>
      <p>
        Local docs: <strong>{apiBase}/docs</strong>
      </p>
      <div className="feature-grid">
        <div className="feature-card">
          <h3>OpenAPI Schema</h3>
          <p>Get the schema at {apiBase}/openapi.json for SDK generation.</p>
        </div>
        <div className="feature-card">
          <h3>Examples</h3>
          <p>Use /v1/solve to submit jobs and /v1/jobs to list them.</p>
        </div>
      </div>
    </div>
  );
}
