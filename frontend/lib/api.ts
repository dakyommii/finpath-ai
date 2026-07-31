import type {
  GoalFormData,
  LifeEventFormData,
  ProfileInput,
  ProfileResult,
  RecommendationResponse,
  RoadmapDetail,
  SimulationRequest,
  SimulationResponse,
} from "@/types/finpath";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`API 요청 실패 (${res.status}): ${detail}`);
  }
  return res.json() as Promise<T>;
}

export function createProfile(input: ProfileInput): Promise<ProfileResult> {
  return postJson("/api/v1/profiles", input);
}

export function createGoal(userId: string, input: GoalFormData) {
  return postJson("/api/v1/goals", { ...input, user_id: userId });
}

export function createLifeEvent(userId: string, input: LifeEventFormData) {
  return postJson("/api/v1/life-events", { ...input, user_id: userId });
}

export function generateRoadmap(userId: string): Promise<RoadmapDetail> {
  return postJson("/api/v1/roadmaps/generate", { user_id: userId });
}

export function generateRecommendations(userId: string): Promise<RecommendationResponse> {
  return postJson("/api/v1/recommendations/generate", { user_id: userId });
}

export function simulateRoadmap(roadmapId: string, input: SimulationRequest): Promise<SimulationResponse> {
  return postJson(`/api/v1/roadmaps/${roadmapId}/simulate`, input);
}
