import StatusBadge from "./StatusBadge";
import EligibilityBadge from "@/components/recommendations/EligibilityBadge";
import type { RecommendationItem, RoadmapStep } from "@/types/finpath";

interface Props {
  step: RoadmapStep;
  relatedRecommendation: RecommendationItem | null;
  onViewDetail: () => void;
}

export default function RoadmapStepCard({ step, relatedRecommendation, onViewDetail }: Props) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-5 text-gray-900">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold text-gray-400">STEP {step.step_order}</p>
          <h3 className="mt-1 text-lg font-bold">{step.title}</h3>
        </div>
        <StatusBadge status={step.status} />
      </div>

      <p className="mt-2 text-xs text-gray-500">
        {step.recommended_start ?? "-"} ~ {step.expected_end ?? "-"}
      </p>

      {step.reason && <p className="mt-3 text-sm text-gray-700">{step.reason}</p>}

      {step.completion_condition && (
        <p className="mt-3 text-sm text-gray-600">
          완료 조건: <span className="font-medium text-gray-900">{step.completion_condition}</span>
        </p>
      )}

      {relatedRecommendation && (
        <div className="mt-4 flex items-center justify-between rounded border border-gray-100 bg-gray-50 p-3">
          <div>
            <p className="text-sm font-medium">{relatedRecommendation.title}</p>
            <div className="mt-1 flex items-center gap-2">
              <EligibilityBadge status={relatedRecommendation.eligibility_status} />
              <span className="text-xs text-gray-500">추천 점수 {relatedRecommendation.priority_score}점</span>
            </div>
          </div>
          <button
            onClick={onViewDetail}
            className="shrink-0 rounded border border-gray-300 bg-white px-3 py-1.5 text-xs font-medium hover:bg-gray-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600"
          >
            자세히 보기
          </button>
        </div>
      )}
    </div>
  );
}
