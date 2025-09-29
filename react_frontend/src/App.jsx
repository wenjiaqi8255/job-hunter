import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
// import { AuthProvider } from './contexts/MockAuthContext';
import HomePage from './pages/HomePage';
import JobListPage from './pages/JobListPage';
import MatchResultsPage from './pages/MatchResultsPage';
import MatchResultsDynamicPage from './pages/MatchResultsDynamicPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import ProfilePage from './pages/ProfilePage';
import ApplicationHistoryPage from './pages/ApplicationHistoryPage';
import MatchingWizard from './components/matching/MatchingWizard';
import JobDetailPage from './pages/JobDetailPage';

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/jobs" element={<JobListPage />} />
          <Route path="/jobs/:jobId" element={<JobDetailPage />} />
          <Route path="/matches" element={<MatchResultsPage />} />
          <Route path="/matches/:session_id" element={<MatchResultsDynamicPage />} />
          <Route path="/matching/start" element={<MatchingWizard />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/applications/history" element={<ApplicationHistoryPage />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
