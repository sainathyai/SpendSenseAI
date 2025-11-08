import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ConfigProvider, theme } from 'antd';
import './App.css';

// Layouts
import AdminLayout from './layouts/AdminLayout';

// Pages
import AllUsers from './pages/AllUsers';
import UserDetail from './pages/UserDetail';
import UserDashboard from './pages/UserDashboard';
import PendingReviews from './pages/PendingReviews';
import DecisionTraces from './pages/DecisionTraces';

// Create React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ConfigProvider
        theme={{
          algorithm: theme.defaultAlgorithm,
          token: {
            colorPrimary: '#5b6cfa',
            colorBgLayout: '#f5f7fb',
            colorBgContainer: '#ffffff',
            colorText: '#1f2440',
            borderRadius: 10,
          },
        }}
      >
        <Router>
          <Routes>
            <Route path="/" element={<AdminLayout />}>
              <Route index element={<Navigate to="/users" replace />} />
              <Route path="users" element={<AllUsers />} />
              <Route path="users/:userId" element={<UserDetail />} />
              <Route path="reviews" element={<PendingReviews />} />
              <Route path="traces" element={<DecisionTraces />} />
            </Route>
            <Route path="/dashboard/:userId" element={<UserDashboard />} />
          </Routes>
        </Router>
      </ConfigProvider>
    </QueryClientProvider>
  );
}

export default App;
