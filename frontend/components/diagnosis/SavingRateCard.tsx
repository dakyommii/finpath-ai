interface Props {
  savingRate: number; // 0~1
  emergencyFundRatio: number; // 0~1
}

function ProgressBar({ label, ratio }: { label: string; ratio: number }) {
  const pct = Math.round(Math.min(Math.max(ratio, 0), 1) * 100);
  return (
    <div>
      <div className="flex justify-between text-sm">
        <span className="text-gray-600">{label}</span>
        <span className="font-medium">{pct}%</span>
      </div>
      <div className="mt-1 h-2 w-full rounded bg-gray-100">
        <div className="h-2 rounded bg-blue-500" style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

export default function SavingRateCard({ savingRate, emergencyFundRatio }: Props) {
  return (
    <div className="space-y-4 rounded-lg border border-gray-200 bg-white p-5 text-gray-900">
      <p className="text-sm text-gray-500">저축 및 비상자금 현황</p>
      <ProgressBar label="저축률" ratio={savingRate} />
      <ProgressBar label="비상자금 충족도" ratio={emergencyFundRatio} />
    </div>
  );
}
