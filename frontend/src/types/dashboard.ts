/**
 * Type definitions for dashboard components
 * Following modern React/TypeScript best practices
 */

export interface Signal {
  signal_type: string;
  window_days: number;
  metrics: Record<string, any>;
  detected_at: string;
}

export interface Persona {
  persona_type: string;
  confidence_score: number;
  supporting_data?: Record<string, any>;
}

export interface Profile {
  customer_id: string;
  primary_persona: Persona;
  secondary_persona?: Persona;
  signals: Signal[];
}

export interface RecommendationItem {
  recommendation_id: string;
  title: string;
  description: string;
  rationale: string;
  content_id?: string;
  offer_id?: string;
  priority: number;
  data_citations?: Record<string, any>;
  content_url?: string;
  eligibility_reason?: string;
}

export interface CounterfactualScenario {
  scenario_id: string;
  title: string;
  description: string;
  current_state: string;
  hypothetical_state: string;
  impact: string;
  time_to_achieve: string;
  confidence: number;
}

export interface Recommendations {
  customer_id: string;
  generated_at: string;
  persona: {
    primary?: string;
    secondary?: string;
    window_30d?: string;
    window_180d?: string;
  };
  education_items: RecommendationItem[];
  partner_offers: RecommendationItem[];
  counterfactual_scenarios: CounterfactualScenario[];
  disclaimer?: string;
}

export interface Account {
  account_id: string;
  type: string;
  subtype: string;
  balances: {
    current: number;
    available: number;
    limit?: number;
  };
}

export interface Balances {
  user_id: string;
  total_assets: number;
  total_debts: number;
  net_worth: number;
  accounts: Account[];
  generated_at: string;
}

export interface FinancialInsights {
  subscriptionCount: number;
  creditUtilization: number;
  savingsBalance: number;
  incomeVariability: number;
  netWorth: number;
  totalDebts: number;
  totalAssets: number;
}

export interface CalculatorModal {
  type: string;
  visible: boolean;
}

