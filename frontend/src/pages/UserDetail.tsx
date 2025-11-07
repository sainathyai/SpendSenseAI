import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Card,
  Spin,
  Alert,
  Space,
  Typography,
  Tag,
  Row,
  Col,
  Statistic,
  Divider,
  Button,
  List,
  Collapse,
} from 'antd';
import {
  UserOutlined,
  DollarOutlined,
  CreditCardOutlined,
  ArrowLeftOutlined,
  CheckCircleOutlined,
  BulbOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';

const { Title, Text } = Typography;

const UserDetail = () => {
  const { userId } = useParams<{ userId: string }>();
  const navigate = useNavigate();

  const { data, isLoading, error } = useQuery({
    queryKey: ['user', userId],
    queryFn: () => api.getProfile(userId!),
    enabled: !!userId,
  });

  const { data: recommendationsData, isLoading: recsLoading } = useQuery({
    queryKey: ['recommendations', userId],
    queryFn: () => api.getRecommendations(userId!, false), // false = skip consent check
    enabled: !!userId,
  });

  if (isLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
        <Spin size="large" />
      </div>
    );
  }

  if (error) {
    return <Alert message="Error loading user profile" type="error" showIcon />;
  }

  const profile = data?.data;
  const primaryPersona = profile?.primary_persona;
  const window30d = profile?.window_30d;
  const window180d = profile?.window_180d;

  return (
    <div style={{ maxWidth: 1280, margin: '0 auto', width: '100%' }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* Back Button */}
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/users')}>
          Back to All Users
        </Button>

        {/* Header Card */}
        <Card
          style={{
            borderRadius: 18,
            background: 'linear-gradient(135deg, #5b7cfa 0%, #8f6bf7 100%)',
            color: '#fff',
            boxShadow: '0 20px 40px rgba(91,124,250,0.3)',
          }}
          styles={{ body: { padding: '32px' } }}
        >
          <Row gutter={24} align="middle">
            <Col xs={24} md={16}>
              <Space direction="vertical" size={12}>
                <Space align="center" size="middle">
                  <UserOutlined style={{ fontSize: 32, color: '#fff' }} />
                  <Title level={2} style={{ color: '#fff', margin: 0 }}>
                    {userId}
                  </Title>
                  <Tag color="success" icon={<CheckCircleOutlined />} style={{ fontSize: 14 }}>
                    Active
                  </Tag>
                </Space>
                {primaryPersona && (
                  <Space>
                    <Tag color="purple" style={{ fontSize: 14, padding: '4px 12px' }}>
                      {primaryPersona.persona_type}
                    </Tag>
                    <Text style={{ color: 'rgba(255,255,255,0.9)' }}>
                      Confidence: {(primaryPersona.confidence_score * 100).toFixed(0)}%
                    </Text>
                  </Space>
                )}
              </Space>
            </Col>
            <Col xs={24} md={8}>
              {primaryPersona?.supporting_data && (
                <Row gutter={[12, 12]}>
                  <Col span={12}>
                    <Statistic
                      title={<span style={{ color: 'rgba(255,255,255,0.8)' }}>Balance</span>}
                      value={primaryPersona.supporting_data.total_balance}
                      prefix="$"
                      precision={2}
                      valueStyle={{ color: '#fff', fontSize: 20 }}
                    />
                  </Col>
                  <Col span={12}>
                    <Statistic
                      title={<span style={{ color: 'rgba(255,255,255,0.8)' }}>Total Limit</span>}
                      value={primaryPersona.supporting_data.total_limit}
                      prefix="$"
                      precision={0}
                      valueStyle={{ color: '#fff', fontSize: 20 }}
                    />
                  </Col>
                </Row>
              )}
            </Col>
          </Row>
        </Card>

        {/* Credit Utilization Cards */}
        <Row gutter={16}>
          <Col xs={24} md={12}>
            <Card
              title={
                <Space>
                  <CreditCardOutlined style={{ color: '#5b6cfa' }} />
                  <span>30-Day Window</span>
                </Space>
              }
              style={{ borderRadius: 16 }}
              styles={{ body: { padding: '24px' } }}
            >
              {window30d && (
                <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                  <Row gutter={16}>
                    <Col span={12}>
                      <Statistic
                        title="Persona"
                        value={window30d.persona_type}
                        valueStyle={{ fontSize: 16 }}
                      />
                    </Col>
                    <Col span={12}>
                      <Statistic
                        title="Confidence"
                        value={(window30d.confidence_score * 100).toFixed(0)}
                        suffix="%"
                        valueStyle={{ fontSize: 16, color: '#52c41a' }}
                      />
                    </Col>
                  </Row>
                  <Divider style={{ margin: '8px 0' }} />
                  {window30d.supporting_data && (
                    <>
                      <Row gutter={16}>
                        <Col span={12}>
                          <Text type="secondary">Utilization</Text>
                          <div style={{ fontSize: 18, fontWeight: 600, color: '#1f2440' }}>
                            {window30d.supporting_data.aggregate_utilization?.toFixed(2)}%
                          </div>
                        </Col>
                        <Col span={12}>
                          <Text type="secondary">Monthly Interest</Text>
                          <div style={{ fontSize: 18, fontWeight: 600, color: '#1f2440' }}>
                            ${window30d.supporting_data.total_monthly_interest?.toFixed(2)}
                          </div>
                        </Col>
                      </Row>
                      <Row gutter={16}>
                        <Col span={12}>
                          <Text type="secondary">Overdue Cards</Text>
                          <div style={{ fontSize: 18, fontWeight: 600, color: window30d.supporting_data.overdue_card_count > 0 ? '#ff4d4f' : '#52c41a' }}>
                            {window30d.supporting_data.overdue_card_count}
                          </div>
                        </Col>
                        <Col span={12}>
                          <Text type="secondary">High Util. Cards</Text>
                          <div style={{ fontSize: 18, fontWeight: 600, color: '#1f2440' }}>
                            {window30d.supporting_data.high_utilization_card_count}
                          </div>
                        </Col>
                      </Row>
                    </>
                  )}
                </Space>
              )}
            </Card>
          </Col>

          <Col xs={24} md={12}>
            <Card
              title={
                <Space>
                  <CreditCardOutlined style={{ color: '#8f6bf7' }} />
                  <span>180-Day Window</span>
                </Space>
              }
              style={{ borderRadius: 16 }}
              styles={{ body: { padding: '24px' } }}
            >
              {window180d && (
                <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                  <Row gutter={16}>
                    <Col span={12}>
                      <Statistic
                        title="Persona"
                        value={window180d.persona_type}
                        valueStyle={{ fontSize: 16 }}
                      />
                    </Col>
                    <Col span={12}>
                      <Statistic
                        title="Confidence"
                        value={(window180d.confidence_score * 100).toFixed(0)}
                        suffix="%"
                        valueStyle={{ fontSize: 16, color: '#52c41a' }}
                      />
                    </Col>
                  </Row>
                  <Divider style={{ margin: '8px 0' }} />
                  {window180d.supporting_data && (
                    <>
                      <Row gutter={16}>
                        <Col span={12}>
                          <Text type="secondary">Utilization</Text>
                          <div style={{ fontSize: 18, fontWeight: 600, color: '#1f2440' }}>
                            {window180d.supporting_data.aggregate_utilization?.toFixed(2)}%
                          </div>
                        </Col>
                        <Col span={12}>
                          <Text type="secondary">Monthly Interest</Text>
                          <div style={{ fontSize: 18, fontWeight: 600, color: '#1f2440' }}>
                            ${window180d.supporting_data.total_monthly_interest?.toFixed(2)}
                          </div>
                        </Col>
                      </Row>
                      <Row gutter={16}>
                        <Col span={12}>
                          <Text type="secondary">Overdue Cards</Text>
                          <div style={{ fontSize: 18, fontWeight: 600, color: window180d.supporting_data.overdue_card_count > 0 ? '#ff4d4f' : '#52c41a' }}>
                            {window180d.supporting_data.overdue_card_count}
                          </div>
                        </Col>
                        <Col span={12}>
                          <Text type="secondary">High Util. Cards</Text>
                          <div style={{ fontSize: 18, fontWeight: 600, color: '#1f2440' }}>
                            {window180d.supporting_data.high_utilization_card_count}
                          </div>
                        </Col>
                      </Row>
                    </>
                  )}
                </Space>
              )}
            </Card>
          </Col>
        </Row>

        {/* Recommendations */}
        <Card
          title={
            <Space>
              <BulbOutlined style={{ color: '#faad14' }} />
              <span>Personalized Recommendations</span>
            </Space>
          }
          style={{ borderRadius: 16 }}
          styles={{ body: { padding: '24px' } }}
          loading={recsLoading}
        >
          {(recommendationsData?.data?.education_items?.length > 0 || recommendationsData?.data?.partner_offers?.length > 0) ? (
            <>
              {/* Education Items */}
              {recommendationsData?.data?.education_items?.length > 0 && (
                <>
                  <Title level={4} style={{ marginTop: 0, marginBottom: 16 }}>
                    📚 Educational Content
                  </Title>
                  <List
                    dataSource={recommendationsData?.data?.education_items || []}
                    style={{ marginBottom: 32 }}
                    renderItem={(rec: any, index: number) => (
                      <List.Item
                        style={{
                          padding: '20px',
                          background: index % 2 === 0 ? '#fafafa' : '#fff',
                          borderRadius: '12px',
                          marginBottom: '12px',
                          border: '1px solid #e5e7eb',
                        }}
                      >
                        <List.Item.Meta
                          avatar={<BulbOutlined style={{ fontSize: 24, color: '#faad14' }} />}
                          title={
                            <Space>
                              <Text strong style={{ fontSize: 16 }}>
                                {rec.title}
                              </Text>
                              <Tag color="blue">Priority {rec.priority}</Tag>
                            </Space>
                          }
                          description={
                            <Space direction="vertical" size="small" style={{ width: '100%' }}>
                              <Text>{rec.description}</Text>
                              <Divider style={{ margin: '8px 0' }} />
                              <Text type="secondary" style={{ fontStyle: 'italic' }}>
                                <strong>Why this matters:</strong> {rec.rationale}
                              </Text>
                            </Space>
                          }
                        />
                      </List.Item>
                    )}
                  />
                </>
              )}
              
              {/* Partner Offers */}
              {recommendationsData?.data?.partner_offers?.length > 0 && (
                <>
                  <Title level={4} style={{ marginBottom: 16 }}>
                    💼 Partner Offers
                  </Title>
                  <List
                    dataSource={recommendationsData?.data?.partner_offers || []}
                    renderItem={(rec: any, index: number) => (
                      <List.Item
                        style={{
                          padding: '20px',
                          background: index % 2 === 0 ? '#fafafa' : '#fff',
                          borderRadius: '12px',
                          marginBottom: '12px',
                          border: '1px solid #e5e7eb',
                        }}
                      >
                        <List.Item.Meta
                          avatar={<DollarOutlined style={{ fontSize: 24, color: '#52c41a' }} />}
                          title={
                            <Space>
                              <Text strong style={{ fontSize: 16 }}>
                                {rec.title}
                              </Text>
                              <Tag color="green">Priority {rec.priority}</Tag>
                            </Space>
                          }
                          description={
                            <Space direction="vertical" size="small" style={{ width: '100%' }}>
                              <Text>{rec.description}</Text>
                              <Divider style={{ margin: '8px 0' }} />
                              <Text type="secondary" style={{ fontStyle: 'italic' }}>
                                <strong>Why this matters:</strong> {rec.rationale}
                              </Text>
                            </Space>
                          }
                        />
                      </List.Item>
                    )}
                  />
                </>
              )}
            </>
          ) : (
            <Alert
              message="No Recommendations Available"
              description="This customer doesn't have any personalized recommendations at this time."
              type="info"
              showIcon
            />
          )}
        </Card>

        {/* Developer Debug - Hidden by default */}
        {import.meta.env.DEV && (
          <Card title="Debug: Raw Profile Data" style={{ borderRadius: 16, opacity: 0.6 }}>
            <Collapse
              items={[
                {
                  key: '1',
                  label: 'View Raw JSON (Dev Only)',
                  children: (
                    <pre style={{
                      background: '#f5f7fb',
                      padding: '16px',
                      borderRadius: '8px',
                      fontSize: '12px',
                      overflow: 'auto',
                      maxHeight: '400px',
                    }}>
                      {JSON.stringify(profile, null, 2)}
                    </pre>
                  ),
                },
              ]}
            />
          </Card>
        )}
      </Space>
    </div>
  );
};

export default UserDetail;

