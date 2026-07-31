interface Props {
  goalType: string | null;
  targetAmount: number | null;
  currentAmount: number;
  eligiblePolicyCount: number;
}

export default function GoalProgressCard({ goalType, targetAmount, currentAmount, eligiblePolicyCount }: Props) {
  const ratio = targetAmount ? Math.min(currentAmount / targetAmount, 1) : null;
  const pct = ratio != null ? Math.round(ratio * 100) : null;

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-5 text-gray-900">
      <p className="text-sm text-gray-500">목표 달성률{goalType ? ` (${goalType})` : ""}</p>
      {pct != null && targetAmount != null ? (
        <>
          <p className="mt-1 text-xl font-bold">{pct}%</p>
          <div className="mt-2 h-2 w-full rounded bg-gray-100">
            <div className="h-2 rounded bg-green-500" style={{ width: `${pct}%` }} />
          </div>
          <p className="mt-2 text-sm text-gray-600">
            현재 {currentAmount.toLocaleString()}원 / 목표 {targetAmount.toLocaleString()}원
          </p>
        </>
      ) : (
        <p className="mt-1 text-sm text-gray-500">목표금액을 입력하면 달성률을 볼 수 있어요.</p>
      )}
      <p className="mt-3 text-sm text-gray-600">
        활용 가능한 정책: <span className="font-medium text-gray-900">{eligiblePolicyCount}개</span>
      </p>
    </div>
  );
}
