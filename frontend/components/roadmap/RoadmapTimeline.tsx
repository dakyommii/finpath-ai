import RoadmapStepCard from "./RoadmapStepCard";
import type { RecommendationItem, RoadmapStep } from "@/types/finpath";

interface Props {
  steps: RoadmapStep[];
  recommendationsByItemId: Map<string, RecommendationItem>;
  onSelectItem: (itemId: string) => void;
}

export default function RoadmapTimeline({ steps, recommendationsByItemId, onSelectItem }: Props) {
  return (
    <ol className="relative space-y-6 border-l-2 border-gray-200 pl-6">
      {steps.map((step) => {
        const relatedRecommendations = (step.related_items ?? [])
          .map((item) => recommendationsByItemId.get(item.item_id))
          .filter((item): item is RecommendationItem => Boolean(item));
        return (
          <li key={step.id} className="relative">
            <span className="absolute -left-[1.95rem] top-2 h-3 w-3 rounded-full bg-blue-500" />
            <RoadmapStepCard
              step={step}
              relatedRecommendations={relatedRecommendations}
              onViewDetail={onSelectItem}
            />
          </li>
        );
      })}
    </ol>
  );
}
