import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AppShell } from '@/components/layout/AppShell';
import { DesignerPage } from '@/pages/DesignerPage';
import { ExecutionsPage } from '@/pages/ExecutionsPage';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route path="/" element={<DesignerPage />} />
          <Route path="/executions" element={<ExecutionsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
