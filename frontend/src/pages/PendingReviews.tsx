import { Card, Empty, Space, Typography } from 'antd';
import { CheckCircleOutlined } from '@ant-design/icons';

const { Title } = Typography;

const PendingReviews = () => {
  return (
    <div style={{ maxWidth: 1280, margin: '0 auto', width: '100%' }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <Card
          style={{ borderRadius: 18, boxShadow: '0 20px 40px rgba(15, 23, 42, 0.08)' }}
          styles={{ body: { padding: '48px 32px' } }}
        >
          <Space direction="vertical" align="center" size="large" style={{ width: '100%' }}>
            <CheckCircleOutlined style={{ fontSize: 72, color: '#52c41a' }} />
            <Title level={3} style={{ margin: 0 }}>
              Pending Reviews
            </Title>
            <Empty
              description="No pending reviews at this time"
              style={{ margin: 0 }}
            />
          </Space>
        </Card>
      </Space>
    </div>
  );
};

export default PendingReviews;

