import { ClearOutlined, RobotOutlined, SendOutlined, UserOutlined } from '@ant-design/icons';
import {
  Alert,
  Button,
  Card,
  Collapse,
  Empty,
  Input,
  Space,
  Spin,
  Table,
  Tag,
  Typography,
} from 'antd';
import { useEffect, useRef, useState } from 'react';
import { api } from '../api/client';

// Define QueryResult type locally to avoid import issues
type QueryResult = {
  success: boolean;
  query: string;
  result?: {
    type?: string;
    customer_id?: string;
    total_assets?: number;
    total_debts?: number;
    net_worth?: number;
    count?: number;
    [key: string]: any;
  };
  error?: string;
  timestamp: string;
};

const { Text, Title } = Typography;
const { TextArea } = Input;

interface ChatMessage {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  result?: QueryResult;
  timestamp: Date;
}

const QueryChat = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await api.executeQuery(input);
      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: response.data.success
          ? '✅ Query executed successfully'
          : `❌ ${response.data.error}`,
        result: response.data,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error: any) {
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: `❌ Error: ${error.response?.data?.detail || error.message}`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setMessages([]);
  };

  const exampleQueries = [
    'list customers',
    'show balances for CUST000001',
    'debt info for CUST000001',
    'subscriptions for CUST000001',
    'transactions for CUST000001',
    'how many customers have cc balances overdue',
    'show customers with highest credit utilization',
    'find customers with no savings accounts',
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Example Queries */}
      {messages.length === 0 && (
        <Card style={{ marginBottom: '16px' }}>
          <Title level={5}>📚 Example Queries</Title>
          <Space direction="vertical" style={{ width: '100%' }}>
            {exampleQueries.map((query) => (
              <Button
                key={query}
                type="text"
                size="small"
                onClick={() => setInput(query)}
                style={{ textAlign: 'left', width: '100%' }}
              >
                <Text code>{query}</Text>
              </Button>
            ))}
          </Space>
        </Card>
      )}

      {/* Chat Messages */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          marginBottom: '16px',
          padding: '8px',
        }}
      >
        {messages.length === 0 ? (
          <Empty
            description="No messages yet. Try asking a question!"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        ) : (
          <Space direction="vertical" size="middle" style={{ width: '100%' }}>
            {messages.map((message) => (
              <ChatMessageItem key={message.id} message={message} />
            ))}
          </Space>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <Card size="small" style={{ borderTop: '1px solid #f0f0f0' }}>
        <Space.Compact style={{ width: '100%' }}>
          <TextArea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onPressEnter={(e) => {
              if (!e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder="Ask a question about customer data..."
            autoSize={{ minRows: 2, maxRows: 4 }}
            disabled={loading}
          />
          <Button
            type="primary"
            icon={loading ? <Spin size="small" /> : <SendOutlined />}
            onClick={handleSend}
            disabled={loading || !input.trim()}
            style={{ height: 'auto' }}
          >
            Send
          </Button>
        </Space.Compact>
        {messages.length > 0 && (
          <Button
            type="text"
            size="small"
            icon={<ClearOutlined />}
            onClick={handleClear}
            style={{ marginTop: '8px' }}
          >
            Clear History
          </Button>
        )}
      </Card>
    </div>
  );
};

// Individual chat message component
const ChatMessageItem = ({ message }: { message: ChatMessage }) => {
  const isUser = message.type === 'user';

  return (
    <div
      style={{
        display: 'flex',
        justifyContent: isUser ? 'flex-end' : 'flex-start',
      }}
    >
      <Card
        size="small"
        style={{
          maxWidth: '80%',
          background: isUser
            ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
            : '#f5f5f5',
          color: isUser ? '#fff' : '#000',
          borderRadius: '12px',
        }}
      >
        <Space direction="vertical" size="small" style={{ width: '100%' }}>
          {/* Header */}
          <Space>
            {isUser ? <UserOutlined /> : <RobotOutlined />}
            <Text strong style={{ color: isUser ? '#fff' : '#000' }}>
              {isUser ? 'You' : 'Assistant'}
            </Text>
            <Text type="secondary" style={{ fontSize: '12px', color: isUser ? 'rgba(255,255,255,0.7)' : undefined }}>
              {message.timestamp.toLocaleTimeString()}
            </Text>
          </Space>

          {/* Content */}
          <Text style={{ color: isUser ? '#fff' : '#000' }}>{message.content}</Text>

          {/* Query Result */}
          {message.result && message.result.success && (
            <QueryResultDisplay result={message.result} />
          )}
        </Space>
      </Card>
    </div>
  );
};

// Display query results
const QueryResultDisplay = ({ result }: { result: QueryResult }) => {
  const data = result.result;
  const resultType = data?.type;

  // Simple display for different result types
  if (!data) return null;

  if (resultType === 'balances' || resultType === 'customer_info') {
    return (
      <Card size="small" style={{ marginTop: '8px', background: 'rgba(255,255,255,0.9)' }}>
        <Space direction="vertical" size="small">
          {data.customer_id && <Tag color="blue">Customer: {data.customer_id}</Tag>}
          {data.total_assets !== undefined && (
            <Text>Assets: ${data.total_assets.toFixed(2)}</Text>
          )}
          {data.total_debts !== undefined && (
            <Text>Debts: ${data.total_debts.toFixed(2)}</Text>
          )}
          {data.net_worth !== undefined && (
            <Text strong style={{ color: data.net_worth >= 0 ? '#52c41a' : '#ff4d4f' }}>
              Net Worth: ${data.net_worth.toFixed(2)}
            </Text>
          )}
        </Space>
      </Card>
    );
  }

  if (resultType === 'customer_list') {
    return (
      <Card size="small" style={{ marginTop: '8px', background: 'rgba(255,255,255,0.9)' }}>
        <Text>Found {data.count} customers</Text>
      </Card>
    );
  }

  if (resultType === 'transactions' && data.transactions && Array.isArray(data.transactions)) {
    const columns = [
      {
        title: 'Date',
        dataIndex: 'date',
        key: 'date',
        width: 120,
        render: (date: string) => {
          try {
            const dateObj = new Date(date);
            return dateObj.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
          } catch {
            return date;
          }
        },
      },
      {
        title: 'Merchant',
        dataIndex: 'name',
        key: 'name',
        ellipsis: true,
      },
      {
        title: 'Category',
        dataIndex: 'category',
        key: 'category',
        width: 180,
        render: (category: string) => (
          <Tag color="blue">{category?.replace(/_/g, ' ').toLowerCase()}</Tag>
        ),
      },
      {
        title: 'Amount',
        dataIndex: 'amount',
        key: 'amount',
        width: 120,
        align: 'right' as const,
        render: (amount: number) => {
          const isPositive = amount > 0;
          return (
            <Text strong style={{ color: isPositive ? '#ff4d4f' : '#52c41a' }}>
              {isPositive ? '-' : '+'}${Math.abs(amount).toFixed(2)}
            </Text>
          );
        },
      },
    ];

    return (
      <Card size="small" style={{ marginTop: '8px', background: 'rgba(255,255,255,0.9)' }}>
        <Space direction="vertical" size="small" style={{ width: '100%' }}>
          {data.customer_id && <Tag color="blue">Customer: {data.customer_id}</Tag>}
          <Text strong>Found {data.count || data.transactions.length} transactions</Text>
          <Table
            columns={columns}
            dataSource={data.transactions.map((t: any, index: number) => ({ ...t, key: t.transaction_id || index }))}
            pagination={false}
            size="small"
            scroll={{ y: 300 }}
          />
        </Space>
      </Card>
    );
  }

  if (resultType === 'debt_info' && data.accounts && Array.isArray(data.accounts)) {
    const columns = [
      {
        title: 'Account',
        dataIndex: 'name',
        key: 'name',
      },
      {
        title: 'Balance',
        dataIndex: 'balance',
        key: 'balance',
        align: 'right' as const,
        render: (balance: number) => `$${balance.toFixed(2)}`,
      },
      {
        title: 'Limit',
        dataIndex: 'limit',
        key: 'limit',
        align: 'right' as const,
        render: (limit: number) => `$${limit.toFixed(2)}`,
      },
      {
        title: 'Utilization',
        dataIndex: 'utilization',
        key: 'utilization',
        align: 'right' as const,
        render: (util: number) => (
          <Tag color={util > 80 ? 'red' : util > 50 ? 'orange' : 'green'}>
            {util.toFixed(1)}%
          </Tag>
        ),
      },
    ];

    return (
      <Card size="small" style={{ marginTop: '8px', background: 'rgba(255,255,255,0.9)' }}>
        <Space direction="vertical" size="small" style={{ width: '100%' }}>
          {data.customer_id && <Tag color="blue">Customer: {data.customer_id}</Tag>}
          <Space>
            <Text>Total Debt: <Text strong>${data.total_debt?.toFixed(2)}</Text></Text>
            <Text>Total Limit: <Text strong>${data.total_limit?.toFixed(2)}</Text></Text>
            <Text>Overall Utilization: <Tag color={data.overall_utilization > 80 ? 'red' : data.overall_utilization > 50 ? 'orange' : 'green'}>{data.overall_utilization?.toFixed(1)}%</Tag></Text>
          </Space>
          <Table
            columns={columns}
            dataSource={data.accounts.map((a: any, index: number) => ({ ...a, key: a.account_id || index }))}
            pagination={false}
            size="small"
          />
        </Space>
      </Card>
    );
  }

  if (resultType === 'subscriptions' && data.subscriptions && Array.isArray(data.subscriptions)) {
    const columns = [
      {
        title: 'Merchant',
        dataIndex: 'merchant_name',
        key: 'merchant_name',
      },
      {
        title: 'Cadence',
        dataIndex: 'cadence',
        key: 'cadence',
        width: 100,
        render: (cadence: string) => <Tag color="purple">{cadence}</Tag>,
      },
      {
        title: 'Monthly Spend',
        dataIndex: 'monthly_recurring_spend',
        key: 'monthly_recurring_spend',
        align: 'right' as const,
        render: (amount: number) => `$${amount.toFixed(2)}`,
      },
      {
        title: 'Status',
        dataIndex: 'is_active',
        key: 'is_active',
        width: 100,
        render: (isActive: boolean) => (
          <Tag color={isActive ? 'green' : 'default'}>{isActive ? 'Active' : 'Inactive'}</Tag>
        ),
      },
    ];

    return (
      <Card size="small" style={{ marginTop: '8px', background: 'rgba(255,255,255,0.9)' }}>
        <Space direction="vertical" size="small" style={{ width: '100%' }}>
          {data.customer_id && <Tag color="blue">Customer: {data.customer_id}</Tag>}
          <Space>
            <Text>Total Subscriptions: <Text strong>{data.subscription_count}</Text></Text>
            <Text>Active: <Text strong>{data.active_subscription_count}</Text></Text>
            <Text>Monthly Recurring: <Text strong>${data.total_monthly_recurring_spend?.toFixed(2)}</Text></Text>
          </Space>
          <Table
            columns={columns}
            dataSource={data.subscriptions.map((s: any, index: number) => ({ ...s, key: s.merchant_name || index }))}
            pagination={false}
            size="small"
            scroll={{ y: 300 }}
          />
        </Space>
      </Card>
    );
  }

  if (resultType === 'overdue_count') {
    return (
      <Card size="small" style={{ marginTop: '8px', background: 'rgba(255,255,255,0.9)' }}>
        <Space direction="vertical" size="small">
          <Text strong style={{ fontSize: '16px', color: (data.count ?? 0) > 0 ? '#ff4d4f' : '#52c41a' }}>
            {data.count ?? 0} customer(s) have overdue credit card balances
          </Text>
          {data.message && <Text type="secondary">{data.message}</Text>}
        </Space>
      </Card>
    );
  }

  if (resultType === 'overdue_customers' && data.customers && Array.isArray(data.customers)) {
    const columns = [
      {
        title: 'Customer ID',
        dataIndex: 'customer_id',
        key: 'customer_id',
      },
      {
        title: 'Overdue Accounts',
        dataIndex: 'overdue_account_count',
        key: 'overdue_account_count',
        align: 'center' as const,
        render: (count: number) => <Tag color="red">{count}</Tag>,
      },
      {
        title: 'Total Overdue Balance',
        dataIndex: 'total_overdue_balance',
        key: 'total_overdue_balance',
        align: 'right' as const,
        render: (balance: number) => (
          <Text strong style={{ color: '#ff4d4f' }}>${balance.toFixed(2)}</Text>
        ),
      },
    ];

    return (
      <Card size="small" style={{ marginTop: '8px', background: 'rgba(255,255,255,0.9)' }}>
        <Space direction="vertical" size="small" style={{ width: '100%' }}>
          <Text strong>Found {data.count} customer(s) with overdue credit card balances</Text>
          <Table
            columns={columns}
            dataSource={data.customers.map((c: any, index: number) => ({ ...c, key: c.customer_id || index }))}
            pagination={false}
            size="small"
            scroll={{ y: 300 }}
          />
        </Space>
      </Card>
    );
  }

  if (resultType === 'sql_result' && data.data && Array.isArray(data.data)) {
    // Get column names from first row
    const firstRow = data.data[0] || {};
    const columns = Object.keys(firstRow).map((key) => ({
      title: key.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase()),
      dataIndex: key,
      key: key,
      render: (value: any) => {
        if (typeof value === 'number') {
          // Format numbers with commas
          if (value % 1 === 0) {
            return value.toLocaleString();
          }
          return value.toFixed(2);
        }
        if (typeof value === 'string' && value.match(/^\d{4}-\d{2}-\d{2}/)) {
          // Format dates
          try {
            const date = new Date(value);
            return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
          } catch {
            return value;
          }
        }
        return value;
      },
    }));

    return (
      <Card size="small" style={{ marginTop: '8px', background: 'rgba(255,255,255,0.9)' }}>
        <Space direction="vertical" size="small" style={{ width: '100%' }}>
          <Text strong>Query executed successfully</Text>
          <Text type="secondary">Found {data.count} result(s)</Text>
          {data.sql_query && (
            <Collapse size="small" style={{ marginBottom: '8px' }}>
              <Collapse.Panel header="View Generated SQL" key="sql">
                <pre style={{ fontSize: '11px', background: '#f5f5f5', padding: '8px', borderRadius: '4px', overflow: 'auto' }}>
                  {data.sql_query}
                </pre>
              </Collapse.Panel>
            </Collapse>
          )}
          {(data.count ?? 0) > 0 ? (
            <Table
              columns={columns}
              dataSource={data.data.map((row: any, index: number) => ({ ...row, key: index }))}
              pagination={(data.count ?? 0) > 10 ? { pageSize: 10 } : false}
              size="small"
              scroll={{ y: 300, x: 'max-content' }}
            />
          ) : (
            <Alert message="No data found" type="info" showIcon />
          )}
        </Space>
      </Card>
    );
  }

  if (resultType === 'overdue_info' && data.accounts && Array.isArray(data.accounts)) {
    const columns = [
      {
        title: 'Account',
        dataIndex: 'name',
        key: 'name',
      },
      {
        title: 'Balance',
        dataIndex: 'balance',
        key: 'balance',
        align: 'right' as const,
        render: (balance: number) => (
          <Text strong style={{ color: '#ff4d4f' }}>${balance.toFixed(2)}</Text>
        ),
      },
      {
        title: 'Limit',
        dataIndex: 'limit',
        key: 'limit',
        align: 'right' as const,
        render: (limit: number) => `$${limit.toFixed(2)}`,
      },
      {
        title: 'Minimum Payment',
        dataIndex: 'minimum_payment',
        key: 'minimum_payment',
        align: 'right' as const,
        render: (amount: number) => `$${amount.toFixed(2)}`,
      },
      {
        title: 'Due Date',
        dataIndex: 'next_payment_due_date',
        key: 'next_payment_due_date',
        render: (date: string) => date || 'N/A',
      },
    ];

    return (
      <Card size="small" style={{ marginTop: '8px', background: 'rgba(255,255,255,0.9)' }}>
        <Space direction="vertical" size="small" style={{ width: '100%' }}>
          {data.customer_id && <Tag color="red">Customer: {data.customer_id}</Tag>}
          <Text strong style={{ color: '#ff4d4f' }}>
            {data.overdue_count} overdue account(s)
          </Text>
          <Table
            columns={columns}
            dataSource={data.accounts.map((a: any, index: number) => ({ ...a, key: a.account_id || index }))}
            pagination={false}
            size="small"
          />
        </Space>
      </Card>
    );
  }

  // Generic JSON display
  return (
    <Collapse
      size="small"
      style={{ marginTop: '8px' }}
      items={[
        {
          key: '1',
          label: 'View Details',
          children: <pre style={{ fontSize: '12px', maxHeight: '300px', overflow: 'auto' }}>
            {JSON.stringify(data, null, 2)}
          </pre>,
        },
      ]}
    />
  );
};

export default QueryChat;

