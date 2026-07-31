interface Props {
  progress: number | null; // 0~1, 완료된 단계 비율
}

export default function RoadmapProgress({ progress }: Props) {
  const pct = Math.round(Math.min(Math.max(progress ?? 0, 0), 1) * 100);
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-5 text-gray-900">
      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-500">현재 진행률</p>
        <p className="text-sm font-semibold">{pct}%</p>
      </div>
      <div className="mt-2 h-2 w-full rounded bg-gray-100">
        <div className="h-2 rounded bg-blue-500" style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}
