import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/layout/Layout';
import { Onboarding } from './pages/Onboarding';
import { Rules } from './pages/Rules';
import { Jobs } from './pages/Jobs';
import { ApiKeys } from './pages/ApiKeys';
import { Events } from './pages/Events';
import { Dashboard } from './pages/Dashboard';
import { SourceDetails } from './pages/SourceDetails';
import { SourceProvider } from './contexts/SourceContext';

function App() {
  return (
    <BrowserRouter>
      <SourceProvider>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Navigate to="/dashboard" replace />} />
            
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="sources" element={<SourceDetails />} />
            <Route path="onboarding" element={<Onboarding />} />
            <Route path="rules" element={<Rules />} />
            <Route path="jobs" element={<Jobs />} />
            <Route path="api-keys" element={<ApiKeys />} />
            <Route path="events" element={<Events />} />
          </Route>
        </Routes>
      </SourceProvider>
    </BrowserRouter>
  );
}

export default App;
