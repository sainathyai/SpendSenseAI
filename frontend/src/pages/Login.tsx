import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card,
  Form,
  Input,
  Button,
  Typography,
  Space,
  Alert,
  Divider,
} from 'antd';
import {
  WalletOutlined,
  UserOutlined,
  LockOutlined,
  ArrowRightOutlined,
} from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';

const { Title, Text } = Typography;

const Login = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onFinish = async (values: { userId: string }) => {
    setLoading(true);
    setError(null);

    try {
      // Verify user exists by checking profile
      const response = await api.getProfile(values.userId);
      
      if (response.data) {
        // User exists, navigate to dashboard
        navigate(`/dashboard/${values.userId}`);
      } else {
        setError('User ID not found. Please check your credentials.');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Unable to verify user. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '20px',
      }}
    >
      <Card
        style={{
          width: '100%',
          maxWidth: 450,
          borderRadius: '16px',
          boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
          border: 'none',
          transition: 'transform 0.3s ease, box-shadow 0.3s ease',
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.transform = 'translateY(-4px)';
          e.currentTarget.style.boxShadow = '0 24px 80px rgba(0,0,0,0.4)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.transform = 'translateY(0)';
          e.currentTarget.style.boxShadow = '0 20px 60px rgba(0,0,0,0.3)';
        }}
        role="main"
        aria-label="Login form"
      >
        <Space direction="vertical" size="large" style={{ width: '100%', textAlign: 'center' }}>
          {/* Logo/Icon */}
          <div style={{ marginBottom: '8px' }}>
            <WalletOutlined
              style={{
                fontSize: '64px',
                color: '#667eea',
                marginBottom: '16px',
                transition: 'transform 0.3s ease',
                animation: 'pulse 2s ease-in-out infinite',
              }}
              aria-hidden="true"
            />
            <Title level={2} style={{ margin: 0, color: '#1f2440' }}>
              SpendSenseAI
            </Title>
            <Text type="secondary" style={{ fontSize: '16px' }}>
              Your Personal Financial Dashboard
            </Text>
          </div>

          <Divider />

          {/* Login Form */}
          <Form
            name="login"
            onFinish={onFinish}
            layout="vertical"
            size="large"
            autoComplete="off"
          >
            {error && (
              <Alert
                message={error}
                type="error"
                showIcon
                closable
                onClose={() => setError(null)}
                style={{ marginBottom: '24px' }}
              />
            )}

            <Form.Item
              name="userId"
              rules={[
                { required: true, message: 'Please enter your User ID' },
                {
                  pattern: /^CUST\d+$/i,
                  message: 'User ID should be in format: CUST000001',
                },
              ]}
            >
              <Input
                prefix={<UserOutlined style={{ color: '#667eea' }} />}
                placeholder="Enter your User ID (e.g., CUST000001)"
                style={{
                  borderRadius: '8px',
                  transition: 'border-color 0.3s ease, box-shadow 0.3s ease',
                }}
                aria-label="User ID input"
                aria-required="true"
                autoFocus
              />
            </Form.Item>

            <Form.Item>
              <Button
                type="primary"
                htmlType="submit"
                loading={loading}
                block
                size="large"
                icon={<ArrowRightOutlined />}
                style={{
                  borderRadius: '8px',
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  border: 'none',
                  height: '48px',
                  fontSize: '16px',
                  fontWeight: 600,
                  transition: 'transform 0.2s ease, box-shadow 0.2s ease',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = 'scale(1.02)';
                  e.currentTarget.style.boxShadow = '0 4px 12px rgba(102, 126, 234, 0.4)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'scale(1)';
                  e.currentTarget.style.boxShadow = 'none';
                }}
                aria-label="Access dashboard button"
              >
                Access Dashboard
              </Button>
            </Form.Item>
          </Form>

          <Divider>Quick Access</Divider>

          <Text type="secondary" style={{ fontSize: '12px' }}>
            Don't have a User ID? Try: <strong>CUST000001</strong> or <strong>CUST000002</strong>
          </Text>
        </Space>
      </Card>
    </div>
  );
};

export default Login;

