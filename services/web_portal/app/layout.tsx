import "./globals.css";

export const metadata = {
  title: "Mentis Optimisation",
  description: "Scheduling and routing optimisation API",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <div className="app-shell">
          <header className="site-header">
            <div className="brand">
              <span className="brand-mark">M</span>
              <div>
                <div className="brand-title">Mentis Optimisation</div>
                <div className="brand-subtitle">Routing & Scheduling API</div>
              </div>
            </div>
            <nav className="site-nav">
              <a href="/">Home</a>
              <a href="/docs">Docs</a>
              <a href="/portal">Portal</a>
            </nav>
          </header>
          <main>{children}</main>
          <footer className="site-footer">
            <div>© 2026 Mentis Consulting</div>
            <div className="footer-links">
              <a href="/docs">API Docs</a>
              <a href="/portal">Developer Portal</a>
            </div>
          </footer>
        </div>
      </body>
    </html>
  );
}
