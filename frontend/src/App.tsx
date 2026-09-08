import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/layout/Layout';
import { Onboarding } from './pages/Onboarding';
import { Rules } from './pages/Rules';
import { Jobs } from './pages/Jobs';
import { ApiKeys } from './pages/ApiKeys';
import { Events } from './pages/Events';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          {/* Redirect root to onboarding (Studio) since it's the primary workflow */}
          <Route index element={<Navigate to="/onboarding" replace />} />
          
          <Route path="onboarding" element={<Onboarding />} />
          <Route path="rules" element={<Rules />} />
          <Route path="jobs" element={<Jobs />} />
          <Route path="api-keys" element={<ApiKeys />} />
          <Route path="events" element={<Events />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
