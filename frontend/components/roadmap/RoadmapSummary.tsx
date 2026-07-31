import type { RoadmapDetail } from "@/types/finpath";

const GOAL_TYPE_LABELS: Record<string, string> = {
  JEONSE: "전세 자금 마련",
  HOME_PURCHASE: "주택 구입",
  SEED_MONEY: "목돈 마련",
  DEBT_REPAYMENT: "부채 상환",
};

interface Props {
  goal: RoadmapDetail["goal"];
  estimatedCompletionDate: string | null;
}

export default function RoadmapSummary({ goal, estimatedCompletionDate }: Props) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-5 text-gray-900">
      <p className="text-sm text-gray-500">최종 금융 목표</p>
      <p className="mt-1 text-xl font-bold">
        {goal ? GOAL_TYPE_LABELS[goal.type] ?? goal.type : "목표 미설정"}
        {goal?.target_amount ? ` · ${goal.target_amount.toLocaleString()}원` : ""}
      </p>
      <p className="mt-2 text-sm text-gray-600">
        예상 목표 달성 시점:{" "}
        <span className="font-medium text-gray-900">{estimatedCompletionDate ?? "산정 불가"}</span>
      </p>
    </div>
  );
}
