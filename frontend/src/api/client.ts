/**
 * API Client for SpendSenseAI
 * Connects to FastAPI backend
 */

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging
apiClient.interceptors.request.use(
  (config) => {
    console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('[API Error]', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// API Types
export type Customer = {
  customer_id: string;
  account_count: number;
  transaction_count: number;
  total_balance: number;
  account_types: Record<string, number>;
};

export type QueryRequest = {
  query: string;
  customer_id?: string;
};

export type QueryResult = {
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

// API Functions
export const api = {
  // Health check
  health: () => apiClient.get('/health'),

  // Users
  getUsers: (limit?: number) =>
    apiClient.get<{ total: number; users: Customer[] }>('/users', { params: { limit } }),

  getUser: (userId: string) =>
    apiClient.get(`/users/${userId}`),

  searchUsers: (query: string, limit: number = 10) =>
    apiClient.get('/users/search/suggestions', { params: { query, limit } }),

  // Profile
  getProfile: (userId: string) =>
    apiClient.get(`/profile/${userId}`),

  // Balances
  getBalances: (userId: string) =>
    apiClient.get(`/balances/${userId}`),

  // Recommendations
  getRecommendations: (userId: string, checkConsent: boolean = false) =>
    apiClient.get(`/recommendations/${userId}`, { params: { check_consent: checkConsent } }),

  // Consent
  getConsent: (userId: string) =>
    apiClient.get(`/consent/${userId}`),

  grantConsent: (userId: string, scope: string = 'all') =>
    apiClient.post('/consent', { user_id: userId, scope }),

  revokeConsent: (userId: string, scope?: string) =>
    apiClient.delete(`/consent/${userId}`, { params: { scope } }),

  // Decision Traces
  getDecisionTrace: (traceId: string) =>
    apiClient.get(`/operator/trace/${traceId}`),

  getDecisionTracesForUser: (userId: string) =>
    apiClient.get(`/operator/traces/${userId}`),

  // Operator endpoints
  getPendingReviews: () =>
    apiClient.get('/operator/review'),

  getUserSignals: (userId: string) =>
    apiClient.get(`/operator/signals/${userId}`),

  getTransactionSummary: (userId: string, days: number = 90) =>
    apiClient.get(`/operator/transactions/${userId}/summary`, { params: { days } }),

  overrideRecommendation: (traceId: string, data: any) =>
    apiClient.post(`/operator/override/${traceId}`, data),

  // Query Tool
  executeQuery: (query: string, customerId?: string) =>
    apiClient.post<QueryResult>('/operator/query', { query, customer_id: customerId }),

  // Calculators
  calculateCreditPayoff: (balance: number, creditLimit: number, apr: number, monthlyPayment: number) =>
    apiClient.post('/calculators/credit-payoff', null, { params: { balance, credit_limit: creditLimit, apr, monthly_payment: monthlyPayment } }),

  calculateEmergencyFund: (monthlyExpenses: number, currentSavings: number, monthlySavings: number, targetMonths: number = 3.0) =>
    apiClient.post('/calculators/emergency-fund', null, { params: { monthly_expenses: monthlyExpenses, current_savings: currentSavings, monthly_savings: monthlySavings, target_months: targetMonths } }),

  analyzeSubscriptions: (userId: string) =>
    apiClient.post(`/calculators/subscription-analysis`, null, { params: { user_id: userId } }),

  planVariableBudget: (userId: string) =>
    apiClient.post(`/calculators/variable-income-budget`, null, { params: { user_id: userId } }),

  getUserCalculators: (userId: string) =>
    apiClient.get(`/calculators/${userId}`),
};

