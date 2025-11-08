import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Table,
  Card,
  Input,
  Select,
  Space,
  Typography,
  Tag,
  Statistic,
  Row,
  Col,
  Button,
  Segmented,
  Tooltip,
  Badge,
} from 'antd';
import type { ColumnsType } from 'antd/es/table';
import {
  UserOutlined,
  SearchOutlined,
  DownloadOutlined,
  ThunderboltOutlined,
  BarChartOutlined,
  ArrowUpOutlined,
} from '@ant-design/icons';
import { api } from '../api/client';
import type { Customer } from '../api/client';

const { Title, Text } = Typography;

const AllUsers = () => {
  const navigate = useNavigate();
  const [filterText, setFilterText] = useState('');
  const [sortField, setSortField] = useState<string>('customer_id');
  const [insightView, setInsightView] = useState<string>('All');

  // Fetch all users
  const { data: usersData, isLoading } = useQuery({
    queryKey: ['users'],
    queryFn: async () => {
      const response = await api.getUsers();
      return response.data;
    },
  });

  const users = usersData?.users || [];
  const total = usersData?.total || 0;

  // Derived metrics
  const totalTransactions = users.reduce((sum, u) => sum + u.transaction_count, 0);
  const totalNetWorth = users.reduce((sum, u) => sum + u.total_balance, 0);
  const avgNetWorth = users.length ? totalNetWorth / users.length : 0;
  const avgAccounts = users.length ? users.reduce((sum, u) => sum + u.account_count, 0) / users.length : 0;
  const totalCreditAccounts = users.reduce((sum, u) => sum + (u.account_types['credit'] || 0), 0);

  const sortedUsers = useMemo(() => {
    let data = [...users];
    switch (insightView) {
      case 'Top Net Worth':
        data.sort((a, b) => b.total_balance - a.total_balance);
        break;
      case 'Most Active':
        data.sort((a, b) => b.transaction_count - a.transaction_count);
        break;
      default:
        break;
    }
    return data;
  }, [users, insightView]);

  const filteredUsers = useMemo(() => {
    return sortedUsers.filter((user) =>
      user.customer_id.toLowerCase().includes(filterText.toLowerCase())
    );
  }, [sortedUsers, filterText]);

  // Table columns with corrected balance display
  const columns: ColumnsType<Customer> = [
    {
      title: 'User ID',
      dataIndex: 'customer_id',
      key: 'customer_id',
      sorter: (a, b) => a.customer_id.localeCompare(b.customer_id),
      render: (text) => (
        <Text strong style={{ color: '#667eea', cursor: 'pointer' }}>
          {text}
        </Text>
      ),
    },
    {
      title: 'Accounts',
      dataIndex: 'account_count',
      key: 'account_count',
      align: 'center' as const,
      sorter: (a, b) => a.account_count - b.account_count,
      render: (count) => (
        <Tag color="blue">{count}</Tag>
      ),
    },
    {
      title: 'Transactions',
      dataIndex: 'transaction_count',
      key: 'transaction_count',
      align: 'center' as const,
      sorter: (a, b) => a.transaction_count - b.transaction_count,
    },
    {
      title: 'Net Worth',
      dataIndex: 'total_balance',
      key: 'total_balance',
      align: 'right' as const,
      sorter: (a, b) => a.total_balance - b.total_balance,
      render: (balance: number) => {
        const isPositive = balance >= 0;
        return (
          <Text
            strong
            style={{
              color: isPositive ? '#52c41a' : '#ff4d4f',
              fontSize: '15px',
            }}
          >
            ${balance.toLocaleString('en-US', {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            })}
          </Text>
        );
      },
    },
    {
      title: 'Account Types',
      dataIndex: 'account_types',
      key: 'account_types',
      render: (types: Record<string, number>) => (
        <Space size={[0, 4]} wrap>
          {Object.entries(types).map(([type, count]) => (
            <Tag key={type} color={type === 'credit' ? 'orange' : 'green'}>
              {type}: {count}
            </Tag>
          ))}
        </Space>
      ),
    },
  ];

  return (
    <div style={{ maxWidth: 1280, margin: '0 auto', width: '100%' }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* Hero Banner */}
        <Card
          className="hero-card"
          style={{
            borderRadius: 24,
            background: 'linear-gradient(135deg, #5b7cfa 0%, #8f6bf7 100%)',
            color: '#fff',
            boxShadow: '0 22px 44px rgba(91,124,250,0.35)',
          }}
          styles={{ body: { padding: '28px 36px' } }}
        >
          <Row gutter={24} align="middle">
            <Col xs={24} md={14}>
              <Space direction="vertical" size={12} style={{ width: '100%' }}>
                <Typography.Title level={3} style={{ color: '#fff', marginBottom: 0 }}>
                  Welcome back, Operator
                </Typography.Title>
                <Typography.Paragraph style={{ color: 'rgba(255,255,255,0.85)', fontSize: 16, marginBottom: 0 }}>
                  Monitor customer activity, track financial health signals, and launch follow-up tasks without leaving this dashboard.
                </Typography.Paragraph>
                <Space size="middle">
                  <Button
                    type="primary"
                    icon={<DownloadOutlined />}
                    style={{ background: '#fff', color: '#4256d0', borderRadius: 24, padding: '0 20px' }}
                  >
                    Export Snapshot
                  </Button>
                  <Tooltip title="Lightning summary of critical changes">
                    <Button icon={<ThunderboltOutlined />} style={{ borderRadius: '50%' }} />
                  </Tooltip>
                </Space>
              </Space>
            </Col>
            <Col xs={24} md={10}>
              <Row gutter={[16, 16]}>
                <Col span={12}>
                  <Statistic
                    title={<span style={{ color: 'rgba(255,255,255,0.7)' }}>Total Users</span>}
                    value={total}
                    prefix={<UserOutlined />}
                    valueStyle={{ color: '#fff', fontSize: 28 }}
                  />
                </Col>
                <Col span={12}>
                  <Statistic
                    title={<span style={{ color: 'rgba(255,255,255,0.7)' }}>Active Accounts</span>}
                    value={users.reduce((sum, u) => sum + u.account_count, 0)}
                    suffix={<span style={{ fontSize: 12, marginLeft: 4 }}>avg {avgAccounts.toFixed(1)} / user</span>}
                    valueStyle={{ color: '#fff', fontSize: 28 }}
                  />
                </Col>
                <Col span={12}>
                  <Statistic
                    title={<span style={{ color: 'rgba(255,255,255,0.7)' }}>Total Transactions</span>}
                    value={totalTransactions}
                    valueStyle={{ color: '#fff', fontSize: 24 }}
                  />
                </Col>
                <Col span={12}>
                  <Statistic
                    title={<span style={{ color: 'rgba(255,255,255,0.7)' }}>Avg Net Worth</span>}
                    precision={2}
                    prefix="$"
                    value={avgNetWorth}
                    valueStyle={{ color: '#fff', fontSize: 24 }}
                  />
                </Col>
              </Row>
            </Col>
          </Row>
        </Card>

        {/* Insight Cards */}
        <Row gutter={18}>
          <Col xs={24} md={8}>
            <Card className="metric-card" styles={{ body: { padding: '20px 24px' } }}>
              <Space direction="vertical" size={4}>
                <Space align="center">
                  <BarChartOutlined style={{ color: '#5b6cfa', fontSize: 20 }} />
                  <Text type="secondary">Credit Utilization</Text>
                </Space>
                <Typography.Title level={4} style={{ margin: 0 }}>
                  {totalCreditAccounts}
                  <Tag color="purple" style={{ marginLeft: 8 }}>credit accounts</Tag>
                </Typography.Title>
                <Text type="secondary">Proactively track high-utilization customers weekly.</Text>
              </Space>
            </Card>
          </Col>
          <Col xs={24} md={8}>
            <Card className="metric-card" styles={{ body: { padding: '20px 24px' } }}>
              <Space direction="vertical" size={4}>
                <Space align="center">
                  <ArrowUpOutlined style={{ color: '#16a34a', fontSize: 20 }} />
                  <Text type="secondary">Portfolio Net Worth</Text>
                </Space>
                <Typography.Title level={4} style={{ margin: 0 }}>
                  ${totalNetWorth.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                </Typography.Title>
                <Text type="secondary">Portfolio-wide net worth across your current customer base.</Text>
              </Space>
            </Card>
          </Col>
          <Col xs={24} md={8}>
            <Card className="metric-card" styles={{ body: { padding: '20px 24px' } }}>
              <Space direction="vertical" size={4}>
                <Space align="center">
                  <Badge status="processing" />
                  <Text type="secondary">Average Accounts / User</Text>
                </Space>
                <Typography.Title level={4} style={{ margin: 0 }}>
                  {avgAccounts.toFixed(1)}
                </Typography.Title>
                <Text type="secondary">Typical customer maintains 2+ linked accounts.</Text>
              </Space>
            </Card>
          </Col>
        </Row>

        {/* Main Table Card */}
        <Card
          style={{ borderRadius: 18, boxShadow: '0 20px 40px rgba(15, 23, 42, 0.08)' }}
          styles={{ body: { padding: '26px 28px' } }}
          title={
            <Space size={16} align="center">
              <UserOutlined style={{ fontSize: 20, color: '#5b6cfa' }} />
              <Title level={4} style={{ margin: 0 }}>
                Customer Directory
              </Title>
              <Tag color="blue" style={{ borderRadius: 16 }}>{filteredUsers.length} visible</Tag>
            </Space>
          }
          extra={
            <Space size="middle">
              <Segmented
                value={insightView}
                onChange={(value) => setInsightView(value as string)}
                options={[
                  { label: 'All', value: 'All' },
                  { label: 'Top Net Worth', value: 'Top Net Worth' },
                  { label: 'Most Active', value: 'Most Active' },
                ]}
              />
              <Input
                placeholder="Filter by User ID"
                prefix={<SearchOutlined />}
                value={filterText}
                onChange={(e) => setFilterText(e.target.value)}
                style={{ width: 220 }}
                allowClear
              />
              <Select
                value={sortField}
                onChange={setSortField}
                style={{ width: 170 }}
                options={[
                  { label: 'Sort by User ID', value: 'customer_id' },
                  { label: 'Sort by Balance', value: 'total_balance' },
                  { label: 'Sort by Accounts', value: 'account_count' },
                  { label: 'Sort by Transactions', value: 'transaction_count' },
                ]}
              />
            </Space>
          }
        >
          <Table
            className="interactive-table"
            dataSource={filteredUsers}
            columns={columns}
            rowKey="customer_id"
            loading={isLoading}
            onRow={(record) => ({
              onClick: () => navigate(`/users/${record.customer_id}`),
              className: 'interactive-row',
            })}
            pagination={{
              pageSize: 15,
              showSizeChanger: true,
              showTotal: (total) => `Total ${total} users`,
            }}
            scroll={{ x: 'max-content' }}
          />
        </Card>

        <Text type="secondary" style={{ display: 'block', textAlign: 'center' }}>
          💡 Tip: Click on any user to deep dive into signals, personas, and recommendation trails.
        </Text>
      </Space>
    </div>
  );
};

export default AllUsers;

