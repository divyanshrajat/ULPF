import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/layout/Layout';
import { Onboarding } from './pages/Onboarding';
import { Rules } from './pages/Rules';
import { Jobs } from './pages/Jobs';
import { Sessions } from './pages/Sessions';
import { ApiKeys } from './pages/ApiKeys';
import { Events } from './pages/Events';
import { Dashboard } from './pages/Dashboard';
import { SourceDetails } from './pages/SourceDetails';
import { SourceProvider } from './contexts/SourceContext';

import { Login } from './pages/Login';

function AuthGuard({ children }: { children: React.ReactNode }) {
  const user = localStorage.getItem('ulpf_user');
  const pass = localStorage.getItem('ulpf_password');
  
  if (!user || !pass) {
    return <Navigate to="/login" replace />;
  }
  
  return <>{children}</>;
}

function App() {
  return (
    <BrowserRouter>
      <SourceProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<AuthGuard><Layout /></AuthGuard>}>
            <Route index element={<Navigate to="/dashboard" replace />} />
            
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="sources" element={<SourceDetails />} />
            <Route path="onboarding" element={<Onboarding />} />
            <Route path="rules" element={<Rules />} />
            <Route path="jobs" element={<Jobs />} />
            <Route path="sessions" element={<Sessions />} />
            <Route path="api-keys" element={<ApiKeys />} />
            <Route path="events" element={<Events />} />
          </Route>
        </Routes>
      </SourceProvider>
    </BrowserRouter>
  );
}

export default App;
