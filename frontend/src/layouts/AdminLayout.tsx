import { useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import {
  Layout,
  Menu,
  FloatButton,
  Drawer,
  Badge,
  Typography,
  Space,
  Tag,
} from 'antd';
import {
  UserOutlined,
  CheckCircleOutlined,
  FileSearchOutlined,
  MessageOutlined,
  DashboardOutlined,
} from '@ant-design/icons';
import QueryChat from '../components/QueryChat';
import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';

const { Header, Sider, Content } = Layout;
const { Title, Text } = Typography;

const AdminLayout = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [chatOpen, setChatOpen] = useState(false);

  // Health check query
  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: () => api.health(),
    refetchInterval: 30000, // Check every 30s
  });

  const menuItems = [
    {
      key: '/users',
      icon: <UserOutlined />,
      label: 'All Users',
    },
    {
      key: '/reviews',
      icon: <CheckCircleOutlined />,
      label: 'Pending Reviews',
    },
    {
      key: '/traces',
      icon: <FileSearchOutlined />,
      label: 'Decision Traces',
    },
  ];

  return (
    <Layout style={{ minHeight: '100vh', background: '#f5f7fb' }}>
      {/* Sidebar */}
      <Sider
        width={250}
        style={{
          background: '#ffffff',
          boxShadow: '2px 0 12px rgba(15,23,42,0.08)',
          borderRight: '1px solid #e5e7eb',
        }}
      >
        {/* Logo/Title */}
        <div style={{ padding: '24px 18px', borderBottom: '1px solid #eef1f6' }}>
          <Space direction="vertical" size={4}>
            <Title level={3} style={{ margin: 0, color: '#1f2440' }}>
              <DashboardOutlined /> SpendSense
            </Title>
            <Text style={{ color: '#667085', fontSize: '13px' }}>
              Operator Dashboard
            </Text>
          </Space>
        </div>

        {/* Navigation Menu */}
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
          style={{
            background: 'transparent',
            border: 'none',
            marginTop: '16px',
            padding: '0 12px',
          }}
          theme="light"
        />

        {/* Status Indicator */}
        <div style={{ 
          position: 'absolute', 
          bottom: 24, 
          left: 18, 
          right: 18,
          padding: '12px',
          background: '#f5f7fb',
          borderRadius: '12px',
          border: '1px solid #e5e7eb',
        }}>
          <Space>
            <Badge status={health?.data?.status === 'healthy' ? 'success' : 'error'} />
            <Text style={{ color: '#475467', fontSize: '13px' }}>
              API {health?.data?.status || 'Disconnected'}
            </Text>
          </Space>
        </div>
      </Sider>

      {/* Main Content */}
      <Layout>
        {/* Header */}
        <Header 
          style={{ 
            background: '#ffffff',
            padding: '0 32px',
            boxShadow: '0 2px 12px rgba(15,23,42,0.08)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <Title level={4} style={{ margin: 0, color: '#1f2440' }}>
            {menuItems.find(item => item.key === location.pathname)?.label || 'Dashboard'}
          </Title>
          
          <Space>
            <Tag color="purple" style={{ borderRadius: 20, padding: '2px 12px' }}>Admin View</Tag>
          </Space>
        </Header>

        {/* Page Content */}
        <Content style={{ 
          margin: '24px',
          padding: '24px',
          background: '#f5f7fb',
          minHeight: 'calc(100vh - 112px)',
        }}>
          <Outlet />
        </Content>
      </Layout>

      {/* Floating Chat Button */}
      <FloatButton
        icon={<MessageOutlined />}
        type="primary"
        style={{ 
          right: 24, 
          bottom: 24,
          width: 60,
          height: 60,
        }}
        onClick={() => setChatOpen(true)}
        tooltip="Open Query Tool"
      />

      {/* Chat Drawer */}
      <Drawer
        title="💬 Query Tool"
        placement="right"
        open={chatOpen}
        onClose={() => setChatOpen(false)}
        width={600}
        styles={{
          header: {
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            color: '#fff',
          },
        }}
      >
        <QueryChat />
      </Drawer>
    </Layout>
  );
};

export default AdminLayout;

