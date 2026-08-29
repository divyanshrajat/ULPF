import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/layout/Layout';
import { Dashboard } from './pages/Dashboard';
import { Onboarding } from './pages/Onboarding';
import { ReviewQueue } from './pages/ReviewQueue';
import { Events } from './pages/Events';
import { TraceExplorer } from './pages/TraceExplorer';
import { SourceDetails } from './pages/SourceDetails';
import { SourceProvider } from './contexts/SourceContext';

import { Processing } from './pages/Processing';
import { Mappings } from './pages/Mappings';
import { Schemas } from './pages/Schemas';
import { Vault } from './pages/Vault';
import { System } from './pages/System';

function App() {
  return (
    <SourceProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="sources" element={<SourceDetails />} />
            <Route path="onboarding" element={<Onboarding />} />
            <Route path="processing" element={<Processing />} />
            <Route path="review" element={<ReviewQueue />} />
            <Route path="events" element={<Events />} />
            <Route path="trace" element={<TraceExplorer />} />
            <Route path="mappings" element={<Mappings />} />
            <Route path="schemas" element={<Schemas />} />
            <Route path="vault" element={<Vault />} />
            <Route path="system" element={<System />} />
            
            {/* Redirect old routes if necessary */}
            <Route path="traceability" element={<Navigate to="/trace" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </SourceProvider>
  );
}

export default App;
