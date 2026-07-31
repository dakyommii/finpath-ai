import type { SimulationResponse } from "@/types/finpath";

interface Props {
  result: SimulationResponse;
}

export default function BeforeAfterSummary({ result }: Props) {
  const months = result.months_saved;
  const monthsLabel =
    months == null ? null : months > 0 ? `예상 ${months}개월 단축` : months < 0 ? `예상 ${-months}개월 지연` : "변화 없음";

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-5 text-gray-900">
      <p className="text-sm text-gray-500">목표 달성 시점 변화</p>
      <div className="mt-2 flex items-center gap-3 text-sm">
        <span className="text-gray-500 line-through">{result.original_estimated_completion_date ?? "-"}</span>
        <span aria-hidden>→</span>
        <span className="text-lg font-bold text-blue-600">{result.simulated_estimated_completion_date ?? "-"}</span>
      </div>
      {monthsLabel && <p className="mt-2 text-sm font-medium text-green-700">{monthsLabel}</p>}
    </div>
  );
}
