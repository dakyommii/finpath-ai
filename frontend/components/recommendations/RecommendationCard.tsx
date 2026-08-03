import EligibilityBadge from "./EligibilityBadge";
import EvidencePanel from "./EvidencePanel";
import type { RecommendationItem } from "@/types/finpath";

interface Props {
  item: RecommendationItem;
  onClose: () => void;
}

export default function RecommendationCard({ item, onClose }: Props) {
  return (
    <div className="rounded-lg border border-blue-200 bg-white p-5 text-gray-900 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs text-gray-500">{item.category}</p>
          <h3 className="mt-1 text-lg font-bold">{item.title}</h3>
          <div className="mt-2 flex items-center gap-2">
            <EligibilityBadge status={item.eligibility_status} />
            <span className="text-xs text-gray-500">추천 점수 {item.priority_score}점</span>
          </div>
        </div>
        <button
          onClick={onClose}
          className="shrink-0 rounded text-sm text-gray-400 hover:text-gray-600 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600"
        >
          닫기
        </button>
      </div>

      <p className="mt-3 text-sm text-gray-700">{item.reason}</p>

      <div className="mt-4">
        <EvidencePanel item={item} />
      </div>
    </div>
  );
}
