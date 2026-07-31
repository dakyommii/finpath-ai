import type { SimulationResponse } from "@/types/finpath";

interface Props {
  result: SimulationResponse;
}

export default function RoadmapDiff({ result }: Props) {
  const hasChanges = result.added_steps.length > 0 || result.removed_steps.length > 0;

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-5 text-gray-900">
      <p className="mb-3 text-sm text-gray-500">로드맵 단계 변화</p>

      {!hasChanges && <p className="text-sm text-gray-500">단계 구성에는 변화가 없습니다.</p>}

      {result.added_steps.length > 0 && (
        <div className="mb-3">
          <p className="text-xs font-semibold text-green-700">추가된 단계</p>
          <ul className="mt-1 space-y-1">
            {result.added_steps.map((title) => (
              <li key={title} className="rounded bg-green-50 px-3 py-1.5 text-sm text-green-800">
                + {title}
              </li>
            ))}
          </ul>
        </div>
      )}

      {result.removed_steps.length > 0 && (
        <div className="mb-3">
          <p className="text-xs font-semibold text-red-700">제외된 단계</p>
          <ul className="mt-1 space-y-1">
            {result.removed_steps.map((title) => (
              <li key={title} className="rounded bg-red-50 px-3 py-1.5 text-sm text-red-800 line-through">
                {title}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="mt-4">
        <p className="text-xs font-semibold text-gray-500">변경 후 전체 단계</p>
        <ol className="mt-1 space-y-1">
          {result.simulated_steps.map((step, i) => (
            <li key={`${step.title}-${i}`} className="flex justify-between text-sm text-gray-700">
              <span>
                {i + 1}. {step.title}
              </span>
              <span className="text-gray-400">{step.expected_end ?? "-"}</span>
            </li>
          ))}
        </ol>
      </div>
    </div>
  );
}
