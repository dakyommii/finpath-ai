export type JobStatus = "EMPLOYED" | "SELF_EMPLOYED" | "UNEMPLOYED" | "STUDENT";
export type MaritalStatus = "SINGLE" | "MARRIED" | "ENGAGED";
export type HousingType = "MONTHLY_RENT" | "JEONSE" | "OWN";
export type GoalType = "JEONSE" | "HOME_PURCHASE" | "SEED_MONEY" | "DEBT_REPAYMENT";
export type LifeEventType = "MARRIAGE" | "CHILDBIRTH" | "RELOCATION" | "JOB_CHANGE";

export type KeywordAxis =
  | "CAREER"
  | "ASSET_PRIORITY"
  | "HOUSING_CONCERN"
  | "FAMILY_PLAN"
  | "FINANCIAL_HEALTH";

// 백엔드는 값 검증을 하지 않고 그대로 저장하므로, 이 표에서 벗어난 값을 보내지 않도록
// UI로만 제어한다 (키워드 임베딩 추천 보강 설계 문서 5.4).
export const KEYWORD_TAXONOMY: Record<KeywordAxis, { label: string; keywords: string[] }> = {
  CAREER: {
    label: "직업/소득 상황",
    keywords: ["이직 준비중", "프리랜서/1인사업", "창업 준비중", "사회초년생(첫 직장)", "소득이 불규칙함", "안정적인 정규직"],
  },
  ASSET_PRIORITY: {
    label: "자산형성 우선순위",
    keywords: ["목돈을 빠르게 모으고 싶음", "절세 혜택이 중요함", "장기 노후 준비", "원금 손실 위험은 피하고 싶음", "투자 수익률을 더 신경씀"],
  },
  HOUSING_CONCERN: {
    label: "주거 관련 걱정",
    keywords: ["전세사기가 걱정됨", "대출 이자 부담이 큼", "보증금 마련이 급함", "월세 부담을 줄이고 싶음", "자가 마련이 최종 목표"],
  },
  FAMILY_PLAN: {
    label: "가족/생애 계획",
    keywords: ["곧 결혼 예정", "이미 신혼부부", "출산·육아 계획 있음", "1인 가구 유지 예정", "부모님과 함께 거주중"],
  },
  FINANCIAL_HEALTH: {
    label: "재무 건전성 우려",
    keywords: ["기존 대출을 정리하고 싶음", "신용점수 관리가 필요함", "비상자금이 부족함", "지출 관리가 어려움"],
  },
};

export interface InterestKeywordInput {
  axis: KeywordAxis;
  keyword: string;
}

export interface ProfileInput {
  age: number;
  region: string;
  job_status: JobStatus;
  annual_income: number;
  marital_status: MaritalStatus;
  housing_type: HousingType;
  liquid_assets: number;
  total_debt?: number;
  monthly_saving: number;
  credit_score_band?: string;
}

export interface ProfileResult extends ProfileInput {
  id: string;
  user_id: string;
}

export interface GoalInput {
  user_id: string;
  goal_type: GoalType;
  target_amount?: number;
  target_date?: string;
  priority?: number;
}

export type GoalFormData = Omit<GoalInput, "user_id">;

export interface LifeEventInput {
  user_id: string;
  event_type: LifeEventType;
  expected_date?: string;
  certainty?: string;
}

export type LifeEventFormData = Omit<LifeEventInput, "user_id">;

export interface RoadmapRelatedItem {
  item_type: string;
  item_id: string;
  title: string;
}

export interface RoadmapStep {
  id: string;
  roadmap_id: string;
  step_order: number;
  title: string;
  status: string;
  recommended_start: string | null;
  expected_end: string | null;
  action: string | null;
  reason: string | null;
  completion_condition: string | null;
  related_items: RoadmapRelatedItem[] | null;
  sources: RoadmapRelatedItem[] | null;
}

export interface RoadmapDetail {
  roadmap_id: string;
  goal: { type: string; target_amount?: number; target_date?: string } | null;
  current_stage: string | null;
  progress: number | null;
  estimated_completion_date: string | null;
  steps: RoadmapStep[];
}

export interface RecommendationItem {
  item_type: string;
  item_id: string;
  title: string;
  category: string;
  eligibility_status: string;
  eligibility_factors: Record<string, string>;
  priority_score: number;
  reason: string;
  benefit_info: Record<string, unknown> | null;
  application_end: string | null;
  official_url: string | null;
}

export interface RecommendationResponse {
  items: RecommendationItem[];
}

export interface DiagnosisData {
  profile: ProfileInput;
  goal: GoalFormData;
  roadmap: RoadmapDetail;
  recommendations: RecommendationResponse;
}

export interface SimulationRequest {
  monthly_saving?: number;
  annual_income?: number;
  life_events?: { event_type: LifeEventType; expected_date?: string }[];
}

export interface SimulationStepSummary {
  title: string;
  status: string;
  recommended_start: string | null;
  expected_end: string | null;
}

export interface SimulationResponse {
  original_estimated_completion_date: string | null;
  simulated_estimated_completion_date: string | null;
  months_saved: number | null;
  added_steps: string[];
  removed_steps: string[];
  original_steps: SimulationStepSummary[];
  simulated_steps: SimulationStepSummary[];
}
