import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { App as AntApp, ConfigProvider, theme } from 'antd';
import './App.css';

// Pages
import Login from './pages/Login';
import UserDashboard from './pages/UserDashboard';

// Create React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function AppUser() {
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
        <AntApp>
          <Router>
            <Routes>
              <Route path="/dashboard/:userId" element={<UserDashboard />} />
              <Route path="/login" element={<Login />} />
              <Route path="/" element={<Login />} />
            </Routes>
          </Router>
        </AntApp>
      </ConfigProvider>
    </QueryClientProvider>
  );
}

export default AppUser;

