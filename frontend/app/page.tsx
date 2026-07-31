"use client";

import { useMemo, useState } from "react";
import OnboardingWizard from "@/components/onboarding/OnboardingWizard";
import FinancialStageCard from "@/components/diagnosis/FinancialStageCard";
import SavingRateCard from "@/components/diagnosis/SavingRateCard";
import GoalProgressCard from "@/components/diagnosis/GoalProgressCard";
import RoadmapSummary from "@/components/roadmap/RoadmapSummary";
import RoadmapProgress from "@/components/roadmap/RoadmapProgress";
import RoadmapTimeline from "@/components/roadmap/RoadmapTimeline";
import RecommendationCard from "@/components/recommendations/RecommendationCard";
import ScenarioControls from "@/components/simulation/ScenarioControls";
import BeforeAfterSummary from "@/components/simulation/BeforeAfterSummary";
import RoadmapDiff from "@/components/simulation/RoadmapDiff";
import { simulateRoadmap } from "@/lib/api";
import type { DiagnosisData, SimulationRequest, SimulationResponse } from "@/types/finpath";

const EMERGENCY_FUND_TARGET = 6_000_000;

type View = "diagnosis" | "roadmap" | "simulation";

const VIEW_LABELS: Record<View, string> = {
  diagnosis: "진단 결과",
  roadmap: "로드맵",
  simulation: "시뮬레이션",
};

export default function Home() {
  const [result, setResult] = useState<DiagnosisData | null>(null);
  const [view, setView] = useState<View>("diagnosis");
  const [selectedItemId, setSelectedItemId] = useState<string | null>(null);
  const [simulationResult, setSimulationResult] = useState<SimulationResponse | null>(null);
  const [simulating, setSimulating] = useState(false);
  const [simulationError, setSimulationError] = useState<string | null>(null);

  const recommendationsByItemId = useMemo(() => {
    const map = new Map<string, DiagnosisData["recommendations"]["items"][number]>();
    result?.recommendations.items.forEach((item) => map.set(item.item_id, item));
    return map;
  }, [result]);

  function handleComplete(data: DiagnosisData) {
    setResult(data);
    setView("diagnosis");
    setSelectedItemId(null);
    setSimulationResult(null);
  }

  function handleReset() {
    setResult(null);
    setView("diagnosis");
    setSelectedItemId(null);
    setSimulationResult(null);
  }

  async function handleSimulate(input: SimulationRequest) {
    if (!result) return;
    setSimulating(true);
    setSimulationError(null);
    try {
      const response = await simulateRoadmap(result.roadmap.roadmap_id, input);
      setSimulationResult(response);
    } catch (e) {
      setSimulationError(e instanceof Error ? e.message : "시뮬레이션 중 오류가 발생했습니다.");
    } finally {
      setSimulating(false);
    }
  }

  if (!result) {
    return (
      <main className="min-h-screen bg-gray-50">
        <OnboardingWizard onComplete={handleComplete} />
      </main>
    );
  }

  const { profile, goal, roadmap, recommendations } = result;
  const savingRate = profile.annual_income > 0 ? (profile.monthly_saving * 12) / profile.annual_income : 0;
  const emergencyFundRatio = profile.liquid_assets / EMERGENCY_FUND_TARGET;
  const eligiblePolicyCount = recommendations.items.filter(
    (item) => item.item_type === "POLICY" && item.eligibility_status !== "NOT_ELIGIBLE"
  ).length;
  const priorityTask = roadmap.steps.find((s) => s.status === "RECOMMENDED_NOW")?.title ?? null;
  const selectedItem = selectedItemId ? recommendationsByItemId.get(selectedItemId) ?? null : null;

  return (
    <main className="min-h-screen bg-gray-50 text-gray-900">
      <div className="mx-auto max-w-3xl space-y-6 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">FinPath AI · {VIEW_LABELS[view]}</h1>
            <p className="mt-1 text-sm text-gray-500">
              입력하신 정보를 바탕으로 분석한 사전 결과입니다. 실제 신청 전 공식 기관에서 최신
              조건을 확인해주세요.
            </p>
          </div>
          <button
            onClick={handleReset}
            className="rounded border border-gray-300 bg-white px-4 py-2 text-sm text-gray-600 hover:bg-gray-100"
          >
            처음부터 다시 입력
          </button>
        </div>

        <nav className="flex gap-2">
          {(Object.keys(VIEW_LABELS) as View[]).map((key) => (
            <button
              key={key}
              onClick={() => setView(key)}
              className={`rounded px-4 py-2 text-sm font-semibold ${
                view === key ? "bg-blue-600 text-white" : "border border-gray-300 bg-white text-gray-600 hover:bg-gray-100"
              }`}
            >
              {VIEW_LABELS[key]}
            </button>
          ))}
        </nav>

        {view === "diagnosis" && (
          <div className="grid gap-4 sm:grid-cols-2">
            <FinancialStageCard stage={roadmap.current_stage} priorityTask={priorityTask} />
            <SavingRateCard savingRate={savingRate} emergencyFundRatio={emergencyFundRatio} />
            <GoalProgressCard
              goalType={goal.goal_type}
              targetAmount={goal.target_amount ?? null}
              currentAmount={profile.liquid_assets}
              eligiblePolicyCount={eligiblePolicyCount}
            />
          </div>
        )}

        {view === "roadmap" && (
          <div className="space-y-6">
            <div className="grid gap-4 sm:grid-cols-2">
              <RoadmapSummary goal={roadmap.goal} estimatedCompletionDate={roadmap.estimated_completion_date} />
              <RoadmapProgress progress={roadmap.progress} />
            </div>

            {selectedItem && <RecommendationCard item={selectedItem} onClose={() => setSelectedItemId(null)} />}

            <RoadmapTimeline
              steps={roadmap.steps}
              recommendationsByItemId={recommendationsByItemId}
              onSelectItem={setSelectedItemId}
            />
          </div>
        )}

        {view === "simulation" && (
          <div className="space-y-6">
            <ScenarioControls
              baselineMonthlySaving={profile.monthly_saving}
              baselineAnnualIncome={profile.annual_income}
              onSimulate={handleSimulate}
              loading={simulating}
            />

            {simulationError && (
              <p className="rounded bg-red-50 p-3 text-sm text-red-600">{simulationError}</p>
            )}

            {simulationResult && (
              <>
                <BeforeAfterSummary result={simulationResult} />
                <RoadmapDiff result={simulationResult} />
              </>
            )}
          </div>
        )}
      </div>
    </main>
  );
}
