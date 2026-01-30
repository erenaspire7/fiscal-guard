// Extension-specific types matching backend models

export interface CartItem {
  item_name: string;
  price: number;
  quantity: number;
  urgency_badge?: string;
  confidence: number;
}

export interface CartAnalysisRequest {
  items: CartItem[];
  page_url: string;
  page_type: "cart" | "checkout" | "product";
}

export interface BudgetAnalysis {
  category?: string;
  current_spent: number;
  limit: number;
  remaining: number;
  percentage_used: number;
  would_exceed: boolean;
  impact_description: string;
}

export interface GoalAnalysis {
  goal_name: string;
  target_amount: number;
  current_amount: number;
  remaining: number;
  deadline?: string;
  impact_description: string;
}

export interface DecisionAnalysis {
  budget_analysis?: BudgetAnalysis;
  affected_goals: GoalAnalysis[];
  purchase_category: string;
  financial_health_score: number;
}

export interface PurchaseDecision {
  score: number;
  decision_category: string;
  reasoning: string;
  analysis: DecisionAnalysis;
  alternatives?: string[];
  conditions?: string[];
}

export interface ItemDecisionResult {
  item_name: string;
  price: number;
  quantity: number;
  total_amount: number;
  urgency_badge?: string;
  decision: PurchaseDecision;
}

export interface AggregateRecommendation {
  total_amount: number;
  overall_score: number;
  overall_recommendation: string;
  items_to_remove: string[];
  items_to_keep: string[];
  budget_impact?: BudgetAnalysis;
  goal_impact: GoalAnalysis[];
}

export interface CartAnalysisResponse {
  items: ItemDecisionResult[];
  aggregate: AggregateRecommendation;
  conversation_id: string;
  requires_clarification: boolean;
}

export interface ExtractedItem {
  item_name: string;
  price: number;
  quantity: number;
  urgency_badge?: string;
  confidence: number;
}

export interface VisionExtractionResult {
  items: ExtractedItem[];
  success: boolean;
  error?: string;
  extractionQuality?: string;
  confidenceScore?: number;
  warnings?: string[];
  validationReport?: {
    is_valid: boolean;
    quality: string;
    confidence: number;
    item_count: number;
    issues: string[];
    recommendations: string[];
  };
}

export interface UserInfo {
  user_id: string;
  email: string;
  full_name?: string;
  profile_picture?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: UserInfo;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  timestamp: string;
}

export interface ChatResponse {
  message: string;
  conversation_id: string;
}
