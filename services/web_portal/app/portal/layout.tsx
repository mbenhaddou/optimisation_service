export default function PortalLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="portal-shell">
      <aside className="portal-sidebar">
        <div className="portal-sidebar-brand">
          <div className="portal-sidebar-title">Operations Portal</div>
          <div className="portal-sidebar-subtitle">
            Route optimization workspace
          </div>
        </div>
        <nav className="portal-nav">
          <a href="/portal">Dashboard</a>
          <a href="/portal/workspace">Workspace</a>
          <a href="/portal/planner">Route Planner</a>
          <a href="/portal/analytics">Analytics</a>
          <a href="/portal/api-tools">API Tools</a>
          <a href="/portal/webhooks">Webhooks</a>
          <a href="/portal/team">Team</a>
          <a href="/portal/reports">Reports</a>
          <a href="/portal/settings">Settings</a>
        </nav>
        <div className="portal-nav-footer">
          <a className="button ghost" href="/portal/login">
            Log in
          </a>
          <a className="button primary" href="/portal/register">
            Register
          </a>
        </div>
      </aside>
      <section className="portal-main">{children}</section>
    </div>
  );
}
