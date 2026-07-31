interface Props {
  stage: string | null;
  priorityTask: string | null;
}

export default function FinancialStageCard({ stage, priorityTask }: Props) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-5 text-gray-900">
      <p className="text-sm text-gray-500">현재 금융 단계</p>
      <p className="mt-1 text-xl font-bold">{stage ?? "분석 중"}</p>
      {priorityTask && (
        <p className="mt-3 text-sm text-gray-600">
          우선 해결 과제: <span className="font-medium text-gray-900">{priorityTask}</span>
        </p>
      )}
    </div>
  );
}
