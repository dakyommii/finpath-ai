interface Props {
  status: string;
}

const STATUS_META: Record<string, { label: string; icon: string; className: string }> = {
  COMPLETED: { label: "완료", icon: "✅", className: "bg-green-100 text-green-700" },
  IN_PROGRESS: { label: "진행 중", icon: "🟡", className: "bg-amber-100 text-amber-700" },
  RECOMMENDED_NOW: { label: "지금 권장", icon: "⭐", className: "bg-blue-100 text-blue-700" },
  PLANNED: { label: "예정", icon: "⚪", className: "bg-gray-100 text-gray-600" },
  NEEDS_CONFIRMATION: { label: "확인 필요", icon: "❓", className: "bg-yellow-100 text-yellow-700" },
  NOT_AVAILABLE: { label: "신청 불가", icon: "🚫", className: "bg-red-100 text-red-700" },
};

export default function StatusBadge({ status }: Props) {
  const meta = STATUS_META[status] ?? { label: status, icon: "•", className: "bg-gray-100 text-gray-600" };
  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ${meta.className}`}>
      <span aria-hidden>{meta.icon}</span>
      {meta.label}
    </span>
  );
}
