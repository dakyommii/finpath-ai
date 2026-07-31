export type JobStatus = "EMPLOYED" | "SELF_EMPLOYED" | "UNEMPLOYED" | "STUDENT";
export type MaritalStatus = "SINGLE" | "MARRIED" | "ENGAGED";
export type HousingType = "MONTHLY_RENT" | "JEONSE" | "OWN";
export type GoalType = "JEONSE" | "HOME_PURCHASE" | "SEED_MONEY" | "DEBT_REPAYMENT";
export type LifeEventType = "MARRIAGE" | "CHILDBIRTH" | "RELOCATION" | "JOB_CHANGE";

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
