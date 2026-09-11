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
      const headers = new Headers();
      headers.set('Authorization', 'Basic ' + btoa(username + ":" + password));
      
      const res = await fetch('/api/health', { headers });
      if (!res.ok) {
        if (res.status === 401) {
          throw new Error("Invalid username or password");
        }
        throw new Error("Login failed");
      }
      
      localStorage.setItem('ulpf_user', username);
      localStorage.setItem('ulpf_password', password);
      
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.message || "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#09090b] flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <h2 className="mt-6 text-center text-3xl font-bold tracking-tight text-white">
          Sign in to your account
        </h2>
        <p className="mt-2 text-center text-sm text-gray-400">
          Universal Log Pre-processing Framework
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-[#18181b] border border-[#27272a] py-8 px-4 shadow-2xl sm:rounded-xl sm:px-10">
          <form className="space-y-6" onSubmit={handleLogin}>
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-gray-300">
                Username
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
                  className="block w-full appearance-none rounded-md border border-[#27272a] px-3 py-2 bg-[#09090b] text-white placeholder-gray-500 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-indigo-500 sm:text-sm transition-colors duration-200"
                  placeholder="admin"
                />
              </div>
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-300">
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
                  className="block w-full appearance-none rounded-md border border-[#27272a] px-3 py-2 bg-[#09090b] text-white placeholder-gray-500 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-indigo-500 sm:text-sm transition-colors duration-200"
                  placeholder="••••••••"
                />
              </div>
            </div>

            {error && (
              <div className="text-red-400 text-sm font-medium">
                {error}
              </div>
            )}

            <div>
              <button
                type="submit"
                disabled={loading}
                className="flex w-full justify-center rounded-md border border-transparent bg-indigo-600 py-2 px-4 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-[#18181b] disabled:opacity-50 transition-colors duration-200"
              >
                {loading ? 'Signing in...' : 'Sign in'}
              </button>
            </div>
            
            <div className="pt-4 border-t border-[#27272a] text-center">
              <p className="text-xs text-gray-400 mb-3">For demo purposes, you can use the default admin credentials:</p>
              <button
                type="button"
                onClick={() => {
                  setUsername('admin');
                  setPassword('ulpf-admin');
                }}
                className="w-full flex justify-center py-2 px-4 border border-[#3f3f46] rounded-md shadow-sm text-sm font-medium text-gray-300 bg-[#27272a] hover:bg-[#3f3f46] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 focus:ring-offset-[#18181b] transition-colors duration-200"
              >
                Use Demo Credentials
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
