import { Card, Empty, Space, Typography } from 'antd';
import { FileSearchOutlined } from '@ant-design/icons';

const { Title } = Typography;

const DecisionTraces = () => {
  return (
    <div style={{ maxWidth: 1280, margin: '0 auto', width: '100%' }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <Card
          style={{ borderRadius: 18, boxShadow: '0 20px 40px rgba(15, 23, 42, 0.08)' }}
          styles={{ body: { padding: '48px 32px' } }}
        >
          <Space direction="vertical" align="center" size="large" style={{ width: '100%' }}>
            <FileSearchOutlined style={{ fontSize: 72, color: '#5b6cfa' }} />
            <Title level={3} style={{ margin: 0 }}>
              Decision Traces
            </Title>
            <Empty
              description="No decision traces available"
              style={{ margin: 0 }}
            />
          </Space>
        </Card>
      </Space>
    </div>
  );
};

export default DecisionTraces;

