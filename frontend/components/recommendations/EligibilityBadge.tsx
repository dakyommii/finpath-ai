interface Props {
  status: string;
}

const ELIGIBILITY_META: Record<string, { label: string; className: string }> = {
  ELIGIBLE: { label: "신청 가능", className: "bg-green-100 text-green-700" },
  CONDITIONAL: { label: "조건부 가능", className: "bg-yellow-100 text-yellow-700" },
  NOT_ELIGIBLE: { label: "현재 신청 어려움", className: "bg-red-100 text-red-700" },
};

export default function EligibilityBadge({ status }: Props) {
  const meta = ELIGIBILITY_META[status] ?? { label: status, className: "bg-gray-100 text-gray-600" };
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${meta.className}`}>
      {meta.label}
    </span>
  );
}
