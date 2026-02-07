"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

const defaultApiBase =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

const STORAGE_KEY = "optimise.portal.settings";
const TOKEN_STORAGE_KEY = "optimise.portal.token";

export default function RegisterPage() {
  const router = useRouter();
  const [apiBase, setApiBase] = useState(defaultApiBase);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [organization, setOrganization] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return;
    try {
      const stored = JSON.parse(raw);
      if (stored.apiBase) setApiBase(stored.apiBase);
    } catch (err) {
      console.warn("Failed to parse portal settings", err);
    }
  }, []);

  const persistSettings = (token: string) => {
    const payload = JSON.stringify({ apiBase, token });
    window.localStorage.setItem(STORAGE_KEY, payload);
    if (token.trim()) {
      window.localStorage.setItem(TOKEN_STORAGE_KEY, token.trim());
    }
  };

  const handleRegister = async () => {
    setIsLoading(true);
    setError("");
    setMessage("");
    try {
      const res = await fetch(`${apiBase}/v1/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, organization }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const msg =
          data?.error?.message || data?.detail || "Registration failed.";
        throw new Error(msg);
      }
      const token = data.access_token;
      persistSettings(token);
      setMessage("Account created. Redirecting to workspace...");
      router.push("/portal/workspace");
    } catch (err: any) {
      setError(err.message || "Registration failed.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="portal-page">
      <div className="portal-auth-card">
        <h1>Create account</h1>
        <p className="portal-subtitle">
          Start optimizing routes with a dedicated workspace.
        </p>

        <div className="portal-form">
          <label>API Base</label>
          <input
            value={apiBase}
            onChange={(event) => setApiBase(event.target.value)}
          />
          <label>Work Email</label>
          <input
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="you@company.com"
          />
          <label>Password</label>
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder="Minimum 8 characters"
          />
          <label>Organization</label>
          <input
            value={organization}
            onChange={(event) => setOrganization(event.target.value)}
            placeholder="Acme Logistics"
          />
          <button className="button primary" onClick={handleRegister} disabled={isLoading}>
            {isLoading ? "Creating..." : "Create account"}
          </button>
        </div>

        {message && <div className="notice-box">{message}</div>}
        {error && <div className="error-box">{error}</div>}

        <div className="portal-auth-footer">
          <span>Already have an account?</span>
          <a className="button ghost" href="/portal/login">
            Log in
          </a>
        </div>
      </div>
    </div>
  );
}
