import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export function Login() {
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('ulpf-admin');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username || !password) {
      setError('Username and password are required');
      return;
    }

    setLoading(true);
    setError('');
    
    // In a real app we'd probably call an API endpoint to verify credentials.
    // For now we just test by hitting health endpoint with Basic Auth, or just store them and let the app fail if they are bad.
    // Since we need to verify credentials to login, let's test them against `/api/v1/stats/overview` or a dedicated health check.
    try {
      const body = new URLSearchParams();
      body.append('username', username);
      body.append('password', password);
      
      const res = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body
      });
      
      if (!res.ok) {
        if (res.status === 401) {
          throw new Error("Invalid username or password");
        }
        throw new Error("Login failed");
      }
      
      const data = await res.json();
      sessionStorage.setItem('ulpf_token', data.access_token);
      
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.message || "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F0F2F5] flex flex-col">
      <div className="flex-1 grid grid-cols-1 md:grid-cols-2 items-center max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-12">
        <div className="pr-0 md:pr-12 flex flex-col items-center text-center">
          <img src="/assets/ulpf_logo.png" alt="ULPF Logo" className="h-[250px] md:h-[400px] w-auto object-contain mb-8" />
          <p className="text-[#4A5D70] text-[15px] leading-relaxed max-w-md mb-8">
            Universal Log Pre-processing Framework: encrypted log ingestion, schema normalization, and a unified log assistant. This prototype is not a live production environment.
          </p>
          
          <div className="text-sm text-[#4A5D70] space-y-3">
            <p>Password for all demo accounts: <span className="font-mono text-slate-900 bg-slate-200 px-1 rounded">ulpf-admin</span></p>
            <p>Use the admin account to access the rule registry and studio.</p>
          </div>
        </div>

        <div className="w-full max-w-md ml-auto">
          <div className="bg-white border border-slate-200 rounded-lg shadow-sm">
            <div className="px-6 py-5 border-b border-slate-100">
              <h3 className="text-lg font-bold text-[#1A2E44]">Secure sign-in</h3>
            </div>
            <div className="px-6 py-6">
              <form className="space-y-6" onSubmit={handleLogin}>
                <div>
                  <label htmlFor="username" className="block text-sm font-medium text-[#1A2E44]">
                    Official demo ID
                  </label>
                  <div className="mt-1">
                    <input
                      id="username"
                      name="username"
                      type="text"
                      autoComplete="username"
                      required
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      className="block w-full appearance-none rounded border border-slate-300 px-3 py-2 bg-white text-slate-900 placeholder-gray-400 shadow-sm focus:border-[#1A2E44] focus:outline-none focus:ring-1 focus:ring-[#1A2E44] sm:text-sm transition-colors duration-200"
                      placeholder="admin"
                    />
                  </div>
                </div>

                <div>
                  <label htmlFor="password" className="block text-sm font-medium text-[#1A2E44]">
                    Password
                  </label>
                  <div className="mt-1">
                    <input
                      id="password"
                      name="password"
                      type="password"
                      autoComplete="current-password"
                      required
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="block w-full appearance-none rounded border border-slate-300 px-3 py-2 bg-white text-slate-900 placeholder-gray-400 shadow-sm focus:border-[#1A2E44] focus:outline-none focus:ring-1 focus:ring-[#1A2E44] sm:text-sm transition-colors duration-200"
                      placeholder="••••••••"
                    />
                  </div>
                </div>

                {error && (
                  <div className="text-red-500 text-sm font-medium">
                    {error}
                  </div>
                )}

                <div>
                  <button
                    type="submit"
                    disabled={loading}
                    className="flex w-full justify-center rounded border border-transparent bg-[#0B1E28] py-2.5 px-4 text-sm font-bold text-white shadow-sm hover:bg-[#152c38] focus:outline-none focus:ring-2 focus:ring-slate-900 focus:ring-offset-2 disabled:opacity-50 transition-colors duration-200"
                  >
                    {loading ? 'Signing in...' : 'Continue'}
                  </button>
                </div>
              </form>
            </div>
          </div>
          
          <div className="mt-8 text-xs text-[#6B7B8C] space-y-1">
            <h4 className="font-bold uppercase tracking-wider text-[#4A5D70] mb-2">DEMO ACCOUNTS</h4>
            <p>admin — Admin (Full Access)</p>
            <p>analyst — Analyst (Read Only)</p>
            <p>auditor — Auditor (Logs only)</p>
          </div>
        </div>
      </div>
    </div>
  );
}
