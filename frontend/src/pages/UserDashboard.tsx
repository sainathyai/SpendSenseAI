import {
  BookOutlined,
  BulbOutlined,
  CalculatorOutlined,
  CheckCircleOutlined,
  CreditCardOutlined,
  DollarOutlined,
  LineChartOutlined,
  RiseOutlined,
  ThunderboltOutlined,
  UserOutlined,
  WarningOutlined,
} from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import {
  Alert,
  Badge,
  Button,
  Card,
  Col,
  Collapse,
  Divider,
  Form,
  InputNumber,
  List,
  Modal,
  Row,
  Space,
  Spin,
  Statistic,
  Tabs,
  Tag,
  Typography,
  message,
} from 'antd';
import React, { useCallback, useState } from 'react';
import { useParams } from 'react-router-dom';
import { api } from '../api/client';
import type {
  CalculatorModal,
  FinancialInsights,
  RecommendationItem,
  Recommendations,
} from '../types/dashboard';

const { Title, Text } = Typography;

const UserDashboard = () => {
  const { userId } = useParams<{ userId: string }>();
  const [activeTab, setActiveTab] = useState('overview');
  const [calculatorModal, setCalculatorModal] = useState<CalculatorModal>({ type: '', visible: false });
  const [calculatorForm] = Form.useForm();
  const [resultModal, setResultModal] = useState<{ visible: boolean; title: string; content: React.ReactNode }>({ visible: false, title: '', content: null });

  // Handler functions following 'handle' prefix convention
  const handleTabChange = useCallback((key: string) => {
    setActiveTab(key);
  }, []);

  const handleCloseCalculator = useCallback(() => {
    setCalculatorModal({ type: '', visible: false });
    calculatorForm.resetFields();
  }, [calculatorForm]);

  const handleKeyDown = useCallback((event: React.KeyboardEvent, action: () => void) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      action();
    }
  }, []);

  const handleAnalyzeSubscriptions = useCallback(async () => {
    if (!userId) return;

    try {
      const response = await api.analyzeSubscriptions(userId);
      setResultModal({
        visible: true,
        title: 'Subscription Analysis',
        content: (
          <div>
            <Statistic
              title="Total Subscriptions"
              value={response.data.total_subscriptions || 0}
              style={{ marginBottom: 16 }}
            />
            <Statistic
              title="Monthly Recurring Spend"
              value={response.data.monthly_recurring_spend || 0}
              prefix="$"
              precision={2}
              style={{ marginBottom: 16 }}
            />
            <Statistic
              title="Annual Recurring Spend"
              value={response.data.annual_recurring_spend || 0}
              prefix="$"
              precision={2}
              style={{ marginBottom: 16 }}
            />
            {response.data.potential_annual_savings > 0 && (
              <Alert
                message={`Potential Annual Savings: $${response.data.potential_annual_savings.toFixed(2)}`}
                type="success"
                showIcon
              />
            )}
          </div>
        ),
      });
    } catch (err: any) {
      message.error('Failed to analyze subscriptions: ' + (err.response?.data?.detail || err.message));
    }
  }, [userId]);

  const handlePlanVariableBudget = useCallback(async () => {
    if (!userId) return;

    try {
      const response = await api.planVariableBudget(userId);
      setResultModal({
        visible: true,
        title: 'Variable Income Budget Plan',
        content: (
          <div>
            <Statistic
              title="Monthly Income"
              value={response.data.monthly_income || 0}
              prefix="$"
              precision={2}
              style={{ marginBottom: 16 }}
            />
            <Divider />
            <Title level={5}>Recommended Budget</Title>
            <List
              dataSource={Object.entries(response.data.recommended_budget || {})}
              renderItem={([key, value]: [string, any]) => (
                <List.Item>
                  <Space style={{ width: '100%', justifyContent: 'space-between' }}>
                    <Text strong>{key.replace(/_/g, ' ')}:</Text>
                    <Text>${typeof value === 'number' ? value.toFixed(2) : value}</Text>
                  </Space>
                </List.Item>
              )}
            />
          </div>
        ),
      });
    } catch (err: any) {
      message.error('Failed to plan budget: ' + (err.response?.data?.detail || err.message));
    }
  }, [userId]);

  const handleCalculateCreditPayoff = useCallback(async (values: any) => {
    try {
      // Calculate credit limit if not provided (estimate as 2x balance or use provided limit)
      const creditLimit = values.creditLimit || values.balance * 2;

      const response = await api.calculateCreditPayoff(
        values.balance,
        creditLimit,
        values.apr,
        values.monthlyPayment
      );

      if (!response || !response.data) {
        message.error('Invalid response from calculator');
        return;
      }

      const data = response.data;

      if (!data || typeof data !== 'object') {
        message.error('Invalid response from calculator');
        return;
      }

      // Show results in a modal
      setResultModal({
        visible: true,
        title: 'Calculation Results',
        content: (
          <div>
            <Statistic
              title="Months to Goal"
              value={data.months_to_goal || 0}
              suffix="months"
              style={{ marginBottom: 16 }}
            />
            <Statistic
              title="Total Interest Paid"
              value={data.total_interest_paid || 0}
              prefix="$"
              precision={2}
              style={{ marginBottom: 16 }}
            />
            <Statistic
              title="Total Payments"
              value={data.total_payments || 0}
              prefix="$"
              precision={2}
            />
          </div>
        ),
      });
      // Don't close calculator modal automatically - let user adjust values and recalculate
    } catch (err: any) {
      message.error('Calculation failed: ' + (err.response?.data?.detail || err.message));
    }
  }, []);

  const handleCalculateEmergencyFund = useCallback(async (values: any) => {
    try {
      const response = await api.calculateEmergencyFund(
        values.monthlyExpenses,
        values.currentSavings,
        values.monthlySavings,
        values.targetMonths || 3.0
      );

      if (!response || !response.data) {
        message.error('Invalid response from calculator');
        return;
      }

      const data = response.data;

      // Show results in a modal
      setResultModal({
        visible: true,
        title: 'Calculation Results',
        content: (
          <div>
            <Statistic
              title="Target Emergency Fund"
              value={data.target_emergency_fund || 0}
              prefix="$"
              precision={2}
              style={{ marginBottom: 16 }}
            />
            <Statistic
              title="Months to Goal"
              value={data.months_to_goal || 0}
              suffix="months"
              style={{ marginBottom: 16 }}
            />
            <Statistic
              title="Remaining Needed"
              value={data.remaining_needed || 0}
              prefix="$"
              precision={2}
            />
            {data.achievable ? (
              <Alert message="Goal is achievable!" type="success" style={{ marginTop: 16 }} />
            ) : (
              <Alert message="Goal may be difficult to achieve. Consider adjusting your savings rate." type="warning" style={{ marginTop: 16 }} />
            )}
          </div>
        ),
      });
      // Don't close calculator modal automatically - let user adjust values and recalculate
    } catch (err: any) {
      message.error('Calculation failed: ' + (err.response?.data?.detail || err.message));
    }
  }, []);

  // Fetch user profile
  const { data: profileData, isLoading: profileLoading } = useQuery({
    queryKey: ['user-profile', userId],
    queryFn: () => api.getProfile(userId!),
    enabled: !!userId,
  });

  // Fetch recommendations
  const { data: recommendationsData, isLoading: recsLoading, error: recsError } = useQuery({
    queryKey: ['user-recommendations', userId],
    queryFn: () => api.getRecommendations(userId!, true), // true = check consent
    enabled: !!userId,
    retry: 1,
  });

  // Fetch financial snapshot
  const { data: balancesData, isLoading: balancesLoading } = useQuery({
    queryKey: ['user-balances', userId],
    queryFn: () => api.getBalances(userId!),
    enabled: !!userId,
  });

  // Synthesize APR for credit cards - MUST be before early returns (Rules of Hooks)
  const synthesizeAPR = useCallback((balance: number, utilization: number): number => {
    const baseAPR = 18.0;
    const utilizationMultiplier = Math.min(utilization / 100, 1.0);
    const balanceMultiplier = balance > 10000 ? 1.2 : 1.0;
    let apr = baseAPR + (utilizationMultiplier * 7);
    apr *= balanceMultiplier;
    return Math.round(apr * 10) / 10;
  }, []);

  // Get balances data (safe to use even if undefined)
  const balances = balancesData?.data;

  // Get credit card accounts with synthesized APR - MUST be before early returns
  const creditCardAccountsList = useCallback(() => {
    if (!balances?.accounts) return [];
    return balances.accounts
      .filter((account: any) => account.type === 'credit' && account.balances?.current > 0)
      .map((account: any) => {
        const balance = account.balances.current || 0;
        const limit = account.balances.limit || 0;
        const utilization = limit > 0 ? (balance / limit) * 100 : 0;
        const apr = account.apr || synthesizeAPR(balance, utilization);
        return {
          account_id: account.account_id,
          balance,
          limit,
          utilization,
          apr,
          subtype: account.subtype,
        };
      });
  }, [balances, synthesizeAPR]);

  // Get primary credit card for auto-population - MUST be before early returns
  const getPrimaryCreditCard = useCallback(() => {
    const cards = creditCardAccountsList();
    if (cards.length === 0) return null;
    return cards.reduce((max: any, card: any) => (card.balance > max.balance ? card : max), cards[0]);
  }, [creditCardAccountsList]);

  // Handle open calculator - MUST be before early returns
  const handleOpenCalculator = useCallback((type: string) => {
    setCalculatorModal({ type, visible: true });
    if (type === 'credit-payoff') {
      const primaryCard = getPrimaryCreditCard();
      if (primaryCard) {
        calculatorForm.setFieldsValue({
          balance: primaryCard.balance,
          apr: primaryCard.apr,
          monthlyPayment: primaryCard.balance * 0.02,
          creditLimit: primaryCard.limit || primaryCard.balance * 2, // Use limit or estimate
        });
      }
    } else if (type === 'emergency-fund') {
      // Get savings balance from balances data
      let currentSavings = 0;
      if (balances?.accounts) {
        currentSavings = balances.accounts
          .filter((account: any) => account.type === 'depository' && account.subtype?.toLowerCase().includes('savings'))
          .reduce((sum: number, account: any) => sum + (account.balances?.current || 0), 0);
      }

      // Estimate monthly expenses from balances or use default
      let monthlyExpenses = 3000; // Default estimate
      if (balances) {
        const totalAssets = balances.total_assets || 0;
        if (totalAssets > 0) {
          // Estimate expenses as 50% of assets divided by 24 (assuming 2 years of expenses in assets)
          monthlyExpenses = Math.max(2000, (totalAssets * 0.5) / 24);
        }
      }

      // Default monthly savings to 10% of expenses
      const monthlySavings = Math.max(200, monthlyExpenses * 0.10);

      calculatorForm.setFieldsValue({
        currentSavings: currentSavings,
        monthlyExpenses: monthlyExpenses,
        monthlySavings: monthlySavings,
        targetMonths: 3.0,
      });
    }
  }, [calculatorForm, getPrimaryCreditCard, balances]);

  // Early returns AFTER all hooks
  if (profileLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!profileData?.data) {
    return <Alert message="Unable to load your profile. Please check your User ID." type="error" showIcon />;
  }

  const profile = profileData.data;
  const primaryPersona = profile.primary_persona;
  const signals = profile.signals || [];
  const recommendations: Recommendations | undefined = recommendationsData?.data;

  // Calculate insights from signals and balances
  const insights: FinancialInsights = {
    subscriptionCount: signals.find((s: any) => s.signal_type === 'subscription')?.metrics?.subscription_count || 0,
    creditUtilization: signals.find((s: any) => s.signal_type === 'credit_utilization')?.metrics?.aggregate_utilization || 0,
    savingsBalance: signals.find((s: any) => s.signal_type === 'savings')?.metrics?.total_savings_balance || 0,
    incomeVariability: signals.find((s: any) => s.signal_type === 'income')?.metrics?.income_variability || 0,
    netWorth: balances ? (balances.total_assets || 0) - (balances.total_debts || 0) : 0,
    totalDebts: balances?.total_debts || 0,
    totalAssets: balances?.total_assets || 0,
  };


  const personaColors: Record<string, string> = {
    high_utilization: 'orange',
    variable_income_budgeter: 'blue',
    subscription_heavy: 'purple',
    savings_builder: 'green',
    financial_fragility: 'red',
  };

  const personaDescriptions: Record<string, string> = {
    high_utilization: "You're managing credit card balances that could benefit from strategic payment planning.",
    variable_income_budgeter: "Your income varies, so flexible budgeting strategies can help you manage cash flow better.",
    subscription_heavy: "You have multiple recurring subscriptions that might be worth reviewing.",
    savings_builder: "You're building your savings—great job! Let's optimize your strategy.",
    financial_fragility: "You're facing some immediate financial challenges. Let's build a buffer and avoid fees.",
  };

  return (
    <div
      style={{
        maxWidth: 1200,
        margin: '0 auto',
        padding: '16px',
        animation: 'fadeIn 0.5s ease-in',
      }}
      className="dashboard-container"
      role="main"
      aria-label="Financial dashboard"
    >
      <Title level={2}>💰 Your Financial Dashboard</Title>
      <Text type="secondary">Welcome back! Here's your personalized financial overview.</Text>
      <Divider />

      {/* Key Insights Section */}
      <Card
        style={{
          marginBottom: 24,
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          border: 'none',
        }}
      >
        <Title level={4} style={{ color: '#fff', marginBottom: 16 }}>
          <ThunderboltOutlined style={{ marginRight: 8 }} />
          Key Financial Insights
        </Title>
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} md={8}>
            <Card
              style={{
                background: 'rgba(255, 255, 255, 0.95)',
                borderRadius: '8px',
                border: 'none',
                transition: 'transform 0.3s ease, box-shadow 0.3s ease',
                cursor: 'pointer',
              }}
              hoverable
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-4px)';
                e.currentTarget.style.boxShadow = '0 8px 24px rgba(0,0,0,0.15)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = 'none';
              }}
              role="article"
              aria-label="Net worth insight card"
            >
              <Space direction="vertical" size="small" style={{ width: '100%' }}>
                <Space>
                  <DollarOutlined style={{ color: insights.netWorth >= 0 ? '#52c41a' : '#ff4d4f', fontSize: '20px' }} />
                  <Text strong>Net Worth</Text>
                </Space>
                <Statistic
                  value={insights.netWorth}
                  prefix="$"
                  precision={2}
                  valueStyle={{
                    color: insights.netWorth >= 0 ? '#52c41a' : '#ff4d4f',
                    fontSize: '24px',
                    fontWeight: 'bold',
                  }}
                />
                <Text type="secondary" style={{ fontSize: '12px' }}>
                  {insights.netWorth >= 0 ? 'Positive' : 'Negative'} net worth
                </Text>
              </Space>
            </Card>
          </Col>
          <Col xs={24} sm={12} md={8}>
            <Card
              style={{
                background: 'rgba(255, 255, 255, 0.95)',
                borderRadius: '8px',
                border: 'none',
                transition: 'transform 0.3s ease, box-shadow 0.3s ease',
                cursor: 'pointer',
              }}
              hoverable
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-4px)';
                e.currentTarget.style.boxShadow = '0 8px 24px rgba(0,0,0,0.15)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = 'none';
              }}
              role="article"
              aria-label="Net worth insight card"
            >
              <Space direction="vertical" size="small" style={{ width: '100%' }}>
                <Space>
                  <CreditCardOutlined style={{ color: insights.creditUtilization > 50 ? '#ff4d4f' : '#52c41a', fontSize: '20px' }} />
                  <Text strong>Credit Utilization</Text>
                </Space>
                <Statistic
                  value={insights.creditUtilization}
                  suffix="%"
                  precision={1}
                  valueStyle={{
                    color: insights.creditUtilization > 50 ? '#ff4d4f' : insights.creditUtilization > 30 ? '#faad14' : '#52c41a',
                    fontSize: '24px',
                    fontWeight: 'bold',
                  }}
                />
                <Text type="secondary" style={{ fontSize: '12px' }}>
                  {insights.creditUtilization > 50 ? 'High' : insights.creditUtilization > 30 ? 'Moderate' : 'Low'} utilization
                </Text>
              </Space>
            </Card>
          </Col>
          <Col xs={24} sm={12} md={8}>
            <Card
              style={{
                background: 'rgba(255, 255, 255, 0.95)',
                borderRadius: '8px',
                border: 'none',
                transition: 'transform 0.3s ease, box-shadow 0.3s ease',
                cursor: 'pointer',
              }}
              hoverable
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-4px)';
                e.currentTarget.style.boxShadow = '0 8px 24px rgba(0,0,0,0.15)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = 'none';
              }}
              role="article"
              aria-label="Net worth insight card"
            >
              <Space direction="vertical" size="small" style={{ width: '100%' }}>
                <Space>
                  <RiseOutlined style={{ color: insights.savingsBalance > 0 ? '#52c41a' : '#faad14', fontSize: '20px' }} />
                  <Text strong>Savings Balance</Text>
                </Space>
                <Statistic
                  value={insights.savingsBalance}
                  prefix="$"
                  precision={2}
                  valueStyle={{
                    color: insights.savingsBalance > 0 ? '#52c41a' : '#faad14',
                    fontSize: '24px',
                    fontWeight: 'bold',
                  }}
                />
                <Text type="secondary" style={{ fontSize: '12px' }}>
                  {insights.savingsBalance > 0 ? 'Growing savings' : 'No savings detected'}
                </Text>
              </Space>
            </Card>
          </Col>
          {insights.subscriptionCount > 0 && (
            <Col xs={24} sm={12} md={8}>
              <Card
                style={{
                  background: 'rgba(255, 255, 255, 0.95)',
                  borderRadius: '8px',
                  border: 'none',
                }}
              >
                <Space direction="vertical" size="small" style={{ width: '100%' }}>
                  <Space>
                    <WarningOutlined style={{ color: '#faad14', fontSize: '20px' }} />
                    <Text strong>Active Subscriptions</Text>
                  </Space>
                  <Statistic
                    value={insights.subscriptionCount}
                    valueStyle={{
                      color: '#faad14',
                      fontSize: '24px',
                      fontWeight: 'bold',
                    }}
                  />
                  <Text type="secondary" style={{ fontSize: '12px' }}>
                    Recurring subscriptions detected
                  </Text>
                </Space>
              </Card>
            </Col>
          )}
          {insights.totalDebts > 0 && (
            <Col xs={24} sm={12} md={8}>
              <Card
                style={{
                  background: 'rgba(255, 255, 255, 0.95)',
                  borderRadius: '8px',
                  border: 'none',
                }}
              >
                <Space direction="vertical" size="small" style={{ width: '100%' }}>
                  <Space>
                    <CreditCardOutlined style={{ color: '#ff4d4f', fontSize: '20px' }} />
                    <Text strong>Total Debt</Text>
                  </Space>
                  <Statistic
                    value={insights.totalDebts}
                    prefix="$"
                    precision={2}
                    valueStyle={{
                      color: '#ff4d4f',
                      fontSize: '24px',
                      fontWeight: 'bold',
                    }}
                  />
                  <Text type="secondary" style={{ fontSize: '12px' }}>
                    Outstanding balances
                  </Text>
                </Space>
              </Card>
            </Col>
          )}
          {insights.totalAssets > 0 && (
            <Col xs={24} sm={12} md={8}>
              <Card
                style={{
                  background: 'rgba(255, 255, 255, 0.95)',
                  borderRadius: '8px',
                  border: 'none',
                }}
              >
                <Space direction="vertical" size="small" style={{ width: '100%' }}>
                  <Space>
                    <DollarOutlined style={{ color: '#52c41a', fontSize: '20px' }} />
                    <Text strong>Total Assets</Text>
                  </Space>
                  <Statistic
                    value={insights.totalAssets}
                    prefix="$"
                    precision={2}
                    valueStyle={{
                      color: '#52c41a',
                      fontSize: '24px',
                      fontWeight: 'bold',
                    }}
                  />
                  <Text type="secondary" style={{ fontSize: '12px' }}>
                    Total account value
                  </Text>
                </Space>
              </Card>
            </Col>
          )}
        </Row>
      </Card>

      <Tabs
        activeKey={activeTab}
        onChange={handleTabChange}
        items={[
          {
            key: 'overview',
            label: (
              <span>
                <UserOutlined /> Overview
              </span>
            ),
            children: (
              <div>
                {/* Persona Card */}
                <Card
                  style={{ marginBottom: 24 }}
                  title={
                    <Space>
                      <UserOutlined />
                      <span>Your Financial Persona</span>
                    </Space>
                  }
                >
                  {primaryPersona && (
                    <Row gutter={16}>
                      <Col span={16}>
                        <Title level={4}>
                          {primaryPersona.persona_type?.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase())}
                        </Title>
                        <Text type="secondary">{personaDescriptions[primaryPersona.persona_type] || 'Your financial behavior shows unique patterns.'}</Text>
                        <div style={{ marginTop: 16 }}>
                          <Tag color={personaColors[primaryPersona.persona_type] || 'default'}>
                            Confidence: {(primaryPersona.confidence_score * 100).toFixed(0)}%
                          </Tag>
                        </div>
                      </Col>
                      <Col span={8}>
                        <Statistic
                          title="Profile Match"
                          value={(primaryPersona.confidence_score * 100).toFixed(0)}
                          suffix="%"
                          valueStyle={{ color: '#3f8600' }}
                        />
                      </Col>
                    </Row>
                  )}
                </Card>

                {/* Financial Summary */}
                {balances && (
                  <Row gutter={16} style={{ marginBottom: 24 }}>
                    <Col span={8}>
                      <Card>
                        <Statistic
                          title="Total Assets"
                          value={balances.total_assets || 0}
                          prefix="$"
                          precision={2}
                          valueStyle={{ color: '#3f8600' }}
                        />
                      </Card>
                    </Col>
                    <Col span={8}>
                      <Card>
                        <Statistic
                          title="Total Debts"
                          value={balances.total_debts || 0}
                          prefix="$"
                          precision={2}
                          valueStyle={{ color: '#cf1322' }}
                        />
                      </Card>
                    </Col>
                    <Col span={8}>
                      <Card>
                        <Statistic
                          title="Net Worth"
                          value={(balances.total_assets || 0) - (balances.total_debts || 0)}
                          prefix="$"
                          precision={2}
                          valueStyle={{
                            color: (balances.total_assets || 0) - (balances.total_debts || 0) >= 0 ? '#3f8600' : '#cf1322',
                          }}
                        />
                      </Card>
                    </Col>
                  </Row>
                )}
              </div>
            ),
          },
          {
            key: 'recommendations',
            label: (
              <span>
                <BulbOutlined /> Recommendations
              </span>
            ),
            children: (
              <div>
                {recsLoading ? (
                  <div style={{ display: 'flex', justifyContent: 'center', padding: '40px 0' }}>
                    <Spin size="large" />
                  </div>
                ) : recsError ? (
                  <Alert
                    message="Unable to load recommendations"
                    description={recsError instanceof Error ? recsError.message : 'Please check your consent settings or try again later.'}
                    type="error"
                    showIcon
                    action={
                      <Button
                        size="small"
                        onClick={() => window.location.reload()}
                        aria-label="Retry loading recommendations"
                      >
                        Retry
                      </Button>
                    }
                  />
                ) : (
                  <>
                    {/* Education Recommendations */}
                    {recommendations?.education_items && recommendations.education_items.length > 0 ? (
                      <div style={{ marginBottom: 24 }}>
                        <Title level={4} style={{ marginBottom: 16 }}>
                          <BulbOutlined style={{ marginRight: 8 }} />
                          Personalized Recommendations
                        </Title>
                        <List
                          dataSource={recommendations.education_items}
                          renderItem={(item: RecommendationItem, index: number) => (
                            <List.Item key={item.recommendation_id}>
                              <Card
                                style={{ width: '100%', marginBottom: 16 }}
                                hoverable
                                role="article"
                                aria-label={`Recommendation ${index + 1}: ${item.title}`}
                              >
                                <Space direction="vertical" size="small" style={{ width: '100%' }}>
                                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                                    <div style={{ flex: 1 }}>
                                      <Title level={5} style={{ margin: 0 }}>
                                        {index + 1}. {item.title}
                                      </Title>
                                      <Text type="secondary">{item.description}</Text>
                                    </div>
                                    <Badge count={index + 1} style={{ backgroundColor: '#5b6cfa' }} />
                                  </div>
                                  {item.rationale && (
                                    <div style={{ marginTop: 12, padding: 12, background: '#f5f7fb', borderRadius: 8 }}>
                                      <Text>
                                        <CheckCircleOutlined style={{ color: '#52c41a', marginRight: 8 }} />
                                        <strong>Why this matters:</strong> {item.rationale}
                                      </Text>
                                    </div>
                                  )}
                                  {item.data_citations && Object.keys(item.data_citations).length > 0 && (
                                    <Collapse
                                      ghost
                                      items={[
                                        {
                                          key: 'data',
                                          label: 'Supporting Data',
                                          children: (
                                            <List
                                              size="small"
                                              dataSource={Object.entries(item.data_citations)}
                                              renderItem={([key, value]: [string, any]) => (
                                                <List.Item>
                                                  <Text strong>{key.replace(/_/g, ' ')}:</Text>{' '}
                                                  {typeof value === 'number' ? `$${value.toLocaleString()}` : String(value)}
                                                </List.Item>
                                              )}
                                            />
                                          ),
                                        },
                                      ]}
                                    />
                                  )}
                                </Space>
                              </Card>
                            </List.Item>
                          )}
                        />
                      </div>
                    ) : (
                      <Alert
                        message="No recommendations available"
                        description="Recommendations will appear here once they are generated. Make sure you have granted consent for personalized recommendations."
                        type="info"
                        showIcon
                        style={{ marginBottom: 24 }}
                      />
                    )}

                    {/* Partner Offers */}
                    {recommendations?.partner_offers && recommendations.partner_offers.length > 0 && (
                      <div>
                        <Title level={4} style={{ marginBottom: 16 }}>
                          💳 Partner Offers
                        </Title>
                        <List
                          dataSource={recommendations.partner_offers}
                          renderItem={(offer: RecommendationItem) => (
                            <List.Item key={offer.recommendation_id}>
                              <Card
                                style={{ width: '100%' }}
                                hoverable
                                role="article"
                                aria-label={`Partner offer: ${offer.title}`}
                              >
                                <Space direction="vertical" size="small" style={{ width: '100%' }}>
                                  <Title level={5} style={{ margin: 0 }}>{offer.title}</Title>
                                  <Text>{offer.description}</Text>
                                  {offer.rationale && (
                                    <Text type="secondary" style={{ fontSize: '14px' }}>
                                      {offer.rationale}
                                    </Text>
                                  )}
                                  {offer.eligibility_reason && (
                                    <Tag color="green">You're eligible: {offer.eligibility_reason}</Tag>
                                  )}
                                  {offer.data_citations && Object.keys(offer.data_citations).length > 0 && (
                                    <Collapse
                                      ghost
                                      items={[
                                        {
                                          key: 'data',
                                          label: 'Supporting Data',
                                          children: (
                                            <List
                                              size="small"
                                              dataSource={Object.entries(offer.data_citations)}
                                              renderItem={([key, value]: [string, any]) => (
                                                <List.Item>
                                                  <Text strong>{key.replace(/_/g, ' ')}:</Text>{' '}
                                                  {typeof value === 'number' ? `$${value.toLocaleString()}` : String(value)}
                                                </List.Item>
                                              )}
                                            />
                                          ),
                                        },
                                      ]}
                                    />
                                  )}
                                </Space>
                              </Card>
                            </List.Item>
                          )}
                        />
                      </div>
                    )}
                  </>
                )}
              </div>
            ),
          },
          {
            key: 'education',
            label: (
              <span>
                <BookOutlined /> Education
              </span>
            ),
            children: (
              <div>
                <Alert
                  message="Educational Content"
                  description="Access personalized financial education content based on your persona and financial situation."
                  type="info"
                  showIcon
                  style={{ marginBottom: 24 }}
                />
                {recsLoading ? (
                  <div style={{ display: 'flex', justifyContent: 'center', padding: '40px 0' }}>
                    <Spin size="large" />
                  </div>
                ) : recommendations?.education_items && recommendations.education_items.length > 0 ? (
                  <List
                    dataSource={recommendations.education_items}
                    renderItem={(item: RecommendationItem, index: number) => (
                      <List.Item key={item.recommendation_id}>
                        <Card
                          style={{ width: '100%', marginBottom: 16 }}
                          hoverable
                          role="article"
                          aria-label={`Educational content ${index + 1}: ${item.title}`}
                        >
                          <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                            <div>
                              <Title level={5} style={{ margin: 0 }}>{item.title}</Title>
                              <Text type="secondary" style={{ display: 'block', marginTop: 8 }}>
                                {item.description}
                              </Text>
                            </div>
                            {item.rationale && (
                              <div style={{ padding: 12, background: '#f5f7fb', borderRadius: 8 }}>
                                <Text>
                                  <CheckCircleOutlined style={{ color: '#52c41a', marginRight: 8 }} />
                                  <strong>Why this matters:</strong> {item.rationale}
                                </Text>
                              </div>
                            )}
                            {item.data_citations && Object.keys(item.data_citations).length > 0 && (
                              <Collapse
                                ghost
                                items={[
                                  {
                                    key: 'data',
                                    label: 'Supporting Data',
                                    children: (
                                      <List
                                        size="small"
                                        dataSource={Object.entries(item.data_citations)}
                                        renderItem={([key, value]: [string, any]) => (
                                          <List.Item>
                                            <Text strong>{key.replace(/_/g, ' ')}:</Text>{' '}
                                            {typeof value === 'number' ? `$${value.toLocaleString()}` : String(value)}
                                          </List.Item>
                                        )}
                                      />
                                    ),
                                  },
                                ]}
                              />
                            )}
                            {item.content_url && (
                              <Button
                                type="primary"
                                href={item.content_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                aria-label={`Read more about ${item.title}`}
                                style={{ minHeight: '44px' }}
                              >
                                Read More
                              </Button>
                            )}
                          </Space>
                        </Card>
                      </List.Item>
                    )}
                  />
                ) : (
                  <Alert
                    message="No educational content available"
                    description="Educational content will appear here once recommendations are generated. Make sure you have granted consent for personalized recommendations."
                    type="info"
                    showIcon
                  />
                )}
              </div>
            ),
          },
          {
            key: 'calculators',
            label: (
              <span>
                <CalculatorOutlined /> Calculators
              </span>
            ),
            children: (
              <div>
                <Row gutter={16}>
                  <Col xs={24} sm={12}>
                    <Card
                      title="Credit Payoff Calculator"
                      extra={
                        <Button
                          type="primary"
                          onClick={() => handleOpenCalculator('credit-payoff')}
                          onKeyDown={(e) => handleKeyDown(e, () => handleOpenCalculator('credit-payoff'))}
                          aria-label="Open credit payoff calculator"
                          style={{ minHeight: '44px' }}
                        >
                          Use Calculator
                        </Button>
                      }
                      hoverable
                    >
                      <Text>Calculate how long it will take to pay off your credit card balance and reach 30% utilization.</Text>
                    </Card>
                  </Col>
                  <Col xs={24} sm={12}>
                    <Card
                      title="Emergency Fund Calculator"
                      extra={
                        <Button
                          type="primary"
                          onClick={() => handleOpenCalculator('emergency-fund')}
                          onKeyDown={(e) => handleKeyDown(e, () => handleOpenCalculator('emergency-fund'))}
                          aria-label="Open emergency fund calculator"
                          style={{ minHeight: '44px' }}
                        >
                          Use Calculator
                        </Button>
                      }
                      hoverable
                    >
                      <Text>Determine how much you need in your emergency fund and how long it will take to reach your goal.</Text>
                    </Card>
                  </Col>
                </Row>
                <Row gutter={16} style={{ marginTop: 16 }}>
                  <Col xs={24} sm={12}>
                    <Card
                      title="Subscription Analyzer"
                      extra={
                        <Button
                          type="primary"
                          onClick={handleAnalyzeSubscriptions}
                          onKeyDown={(e) => handleKeyDown(e, handleAnalyzeSubscriptions)}
                          aria-label="Analyze subscriptions"
                          style={{ minHeight: '44px' }}
                        >
                          Analyze
                        </Button>
                      }
                      hoverable
                    >
                      <Text>Analyze your subscription costs and potential savings from cancellations.</Text>
                    </Card>
                  </Col>
                  <Col xs={24} sm={12}>
                    <Card
                      title="Variable Income Budget Planner"
                      extra={
                        <Button
                          type="primary"
                          onClick={handlePlanVariableBudget}
                          onKeyDown={(e) => handleKeyDown(e, handlePlanVariableBudget)}
                          aria-label="Plan variable income budget"
                          style={{ minHeight: '44px' }}
                        >
                          Plan Budget
                        </Button>
                      }
                      hoverable
                    >
                      <Text>Plan your budget for variable income situations.</Text>
                    </Card>
                  </Col>
                </Row>

                {/* Calculator Modals */}
                <Modal
                  title="Credit Payoff Calculator"
                  open={calculatorModal.type === 'credit-payoff' && calculatorModal.visible}
                  onCancel={handleCloseCalculator}
                  footer={null}
                  width={600}
                  aria-labelledby="credit-payoff-calculator-title"
                >
                  {creditCardAccountsList().length > 0 && (
                    <Alert
                      message="Credit Card Detected"
                      description={`Using data from your ${getPrimaryCreditCard()?.subtype || 'credit card'} account. You can modify the values below.`}
                      type="info"
                      showIcon
                      style={{ marginBottom: 16 }}
                    />
                  )}
                  <Form
                    form={calculatorForm}
                    layout="vertical"
                    onFinish={handleCalculateCreditPayoff}
                  >
                    <Form.Item
                      name="balance"
                      label="Current Balance"
                      rules={[{ required: true, message: 'Please enter your current balance' }]}
                      tooltip="Your current credit card balance"
                    >
                      <InputNumber
                        prefix="$"
                        style={{ width: '100%' }}
                        min={0}
                        step={100}
                        placeholder="Enter current credit card balance"
                        aria-label="Current credit card balance"
                      />
                    </Form.Item>
                    <Form.Item
                      name="apr"
                      label="Annual Percentage Rate (APR)"
                      rules={[{ required: true, message: 'Please enter APR' }]}
                      tooltip="Estimated APR based on your credit utilization. You can adjust this value."
                    >
                      <InputNumber
                        suffix="%"
                        style={{ width: '100%' }}
                        min={0}
                        max={100}
                        step={0.1}
                        placeholder="Enter APR (e.g., 22.0)"
                        aria-label="Annual percentage rate"
                      />
                    </Form.Item>
                    <Form.Item
                      name="creditLimit"
                      label="Credit Limit"
                      rules={[{ required: true, message: 'Please enter credit limit' }]}
                      tooltip="Your credit card limit (used to calculate target utilization)"
                    >
                      <InputNumber
                        prefix="$"
                        style={{ width: '100%' }}
                        min={0}
                        step={500}
                        placeholder="Enter credit card limit"
                        aria-label="Credit card limit"
                      />
                    </Form.Item>
                    <Form.Item
                      name="monthlyPayment"
                      label="Monthly Payment"
                      rules={[{ required: true, message: 'Please enter monthly payment' }]}
                      tooltip="The amount you plan to pay each month"
                    >
                      <InputNumber
                        prefix="$"
                        style={{ width: '100%' }}
                        min={0}
                        step={10}
                        placeholder="Enter monthly payment amount"
                        aria-label="Monthly payment amount"
                      />
                    </Form.Item>
                    {creditCardAccountsList().length > 1 && (
                      <Form.Item label="Other Credit Cards">
                        <Collapse
                          ghost
                          items={[
                            {
                              key: 'other-cards',
                              label: `View ${creditCardAccountsList().length - 1} other credit card${creditCardAccountsList().length > 2 ? 's' : ''}`,
                              children: (
                                <List
                                  size="small"
                                  dataSource={creditCardAccountsList().filter((card: any) => card.account_id !== getPrimaryCreditCard()?.account_id)}
                                  renderItem={(card: any) => (
                                    <List.Item>
                                      <Space style={{ width: '100%', justifyContent: 'space-between' }}>
                                        <div>
                                          <Text strong>{card.subtype}</Text>
                                          <br />
                                          <Text type="secondary">Balance: ${card.balance.toLocaleString()}</Text>
                                        </div>
                                        <Button
                                          size="small"
                                          onClick={() => {
                                            calculatorForm.setFieldsValue({
                                              balance: card.balance,
                                              apr: card.apr,
                                              monthlyPayment: card.balance * 0.02,
                                            });
                                          }}
                                          aria-label={`Use ${card.subtype} card data`}
                                        >
                                          Use This Card
                                        </Button>
                                      </Space>
                                    </List.Item>
                                  )}
                                />
                              ),
                            },
                          ]}
                        />
                      </Form.Item>
                    )}
                    <Form.Item>
                      <Button
                        type="primary"
                        htmlType="submit"
                        block
                        aria-label="Calculate results"
                        style={{ minHeight: '44px' }}
                      >
                        Calculate
                      </Button>
                    </Form.Item>
                  </Form>
                </Modal>

                <Modal
                  title="Emergency Fund Calculator"
                  open={calculatorModal.type === 'emergency-fund' && calculatorModal.visible}
                  onCancel={handleCloseCalculator}
                  footer={null}
                  width={600}
                  aria-labelledby="emergency-fund-calculator-title"
                >
                  {(() => {
                    // Get savings balance from balances data for alert
                    const currentSavings = balances?.accounts
                      ? balances.accounts
                        .filter((account: any) => account.type === 'depository' && account.subtype?.toLowerCase().includes('savings'))
                        .reduce((sum: number, account: any) => sum + (account.balances?.current || 0), 0)
                      : 0;

                    return currentSavings > 0 ? (
                      <Alert
                        message="Savings Account Detected"
                        description={`Using data from your savings account ($${currentSavings.toLocaleString()}). You can modify the values below.`}
                        type="info"
                        showIcon
                        style={{ marginBottom: 16 }}
                      />
                    ) : null;
                  })()}
                  <Form
                    form={calculatorForm}
                    layout="vertical"
                    onFinish={handleCalculateEmergencyFund}
                  >
                    <Form.Item
                      name="monthlyExpenses"
                      label="Monthly Expenses"
                      rules={[{ required: true, message: 'Please enter monthly expenses' }]}
                      tooltip="Your average monthly expenses (estimated from your account data)"
                    >
                      <InputNumber
                        prefix="$"
                        style={{ width: '100%' }}
                        min={0}
                        step={100}
                        placeholder="Enter your monthly expenses"
                        aria-label="Monthly expenses"
                      />
                    </Form.Item>
                    <Form.Item
                      name="currentSavings"
                      label="Current Savings"
                      rules={[{ required: true, message: 'Please enter current savings' }]}
                      tooltip="Your current savings balance (auto-populated from your accounts)"
                    >
                      <InputNumber
                        prefix="$"
                        style={{ width: '100%' }}
                        min={0}
                        step={100}
                        placeholder="Enter your current savings"
                        aria-label="Current savings balance"
                      />
                    </Form.Item>
                    <Form.Item
                      name="monthlySavings"
                      label="Monthly Savings"
                      rules={[{ required: true, message: 'Please enter monthly savings' }]}
                      tooltip="The amount you can save each month (defaults to 10% of expenses)"
                    >
                      <InputNumber
                        prefix="$"
                        style={{ width: '100%' }}
                        min={0}
                        step={50}
                        placeholder="Enter how much you can save per month"
                        aria-label="Monthly savings amount"
                      />
                    </Form.Item>
                    <Form.Item
                      name="targetMonths"
                      label="Target Months of Coverage"
                      initialValue={3.0}
                      tooltip="How many months of expenses you want to save (default: 3 months)"
                    >
                      <InputNumber
                        style={{ width: '100%' }}
                        min={1}
                        max={12}
                        step={0.5}
                        placeholder="Months of expenses to cover (default: 3)"
                        aria-label="Target months of coverage"
                      />
                    </Form.Item>
                    <Form.Item>
                      <Button
                        type="primary"
                        htmlType="submit"
                        block
                        aria-label="Calculate emergency fund"
                        style={{ minHeight: '44px' }}
                      >
                        Calculate
                      </Button>
                    </Form.Item>
                  </Form>
                </Modal>
              </div>
            ),
          },
          {
            key: 'snapshot',
            label: (
              <span>
                <LineChartOutlined /> Financial Snapshot
              </span>
            ),
            children: (
              <div>
                {balancesLoading ? (
                  <Spin size="large" />
                ) : balances ? (
                  <Row gutter={16}>
                    <Col span={12}>
                      <Card title="Account Balances">
                        {balances.accounts && balances.accounts.length > 0 ? (
                          <List
                            dataSource={balances.accounts}
                            renderItem={(account: any) => (
                              <List.Item>
                                <Space>
                                  <CreditCardOutlined />
                                  <div>
                                    <Text strong>{account.type} - {account.subtype}</Text>
                                    <br />
                                    <Text>Balance: ${account.balances?.current?.toLocaleString() || 0}</Text>
                                  </div>
                                </Space>
                              </List.Item>
                            )}
                          />
                        ) : (
                          <Text type="secondary">No account information available.</Text>
                        )}
                      </Card>
                    </Col>
                    <Col span={12}>
                      <Card title="Financial Summary">
                        <Space direction="vertical" style={{ width: '100%' }}>
                          <Statistic title="Total Assets" value={balances.total_assets || 0} prefix="$" />
                          <Statistic title="Total Debts" value={balances.total_debts || 0} prefix="$" />
                          <Divider />
                          <Statistic
                            title="Net Worth"
                            value={(balances.total_assets || 0) - (balances.total_debts || 0)}
                            prefix="$"
                            valueStyle={{
                              color: (balances.total_assets || 0) - (balances.total_debts || 0) >= 0 ? '#3f8600' : '#cf1322',
                            }}
                          />
                        </Space>
                      </Card>
                    </Col>
                  </Row>
                ) : (
                  <Alert message="Unable to load financial snapshot." type="warning" showIcon />
                )}
              </div>
            ),
          },
        ]}
      />

      {/* Result Modal for Calculator Results */}
      <Modal
        title={resultModal.title}
        open={resultModal.visible}
        onCancel={() => setResultModal({ visible: false, title: '', content: null })}
        width={600}
        footer={[
          <Button key="ok" type="primary" onClick={() => setResultModal({ visible: false, title: '', content: null })}>
            OK
          </Button>
        ]}
      >
        {resultModal.content}
      </Modal>
    </div>
  );
};

export default UserDashboard;

