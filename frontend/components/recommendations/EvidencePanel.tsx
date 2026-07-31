import type { RecommendationItem } from "@/types/finpath";

const FACTOR_LABELS: Record<string, string> = {
  age: "나이 조건",
  income: "소득 조건",
  region: "지역 조건",
  marital_status: "혼인 조건",
  homeownership: "무주택 조건",
};

const FACTOR_STATUS_LABELS: Record<string, string> = {
  MET: "충족",
  NOT_MET: "미충족",
  NEEDS_CONFIRMATION: "확인 필요",
  NOT_APPLICABLE: "해당 없음",
};

const FACTOR_STATUS_CLASS: Record<string, string> = {
  MET: "text-green-700",
  NOT_MET: "text-red-700",
  NEEDS_CONFIRMATION: "text-yellow-700",
  NOT_APPLICABLE: "text-gray-400",
};

const BENEFIT_FIELD_LABELS: Record<string, string> = {
  support_content: "지원 내용",
  application_agency: "신청기관",
  required_documents: "준비서류",
  tax_benefit: "세제혜택",
  notes: "참고사항",
};

function formatBenefitValue(value: unknown): string {
  if (Array.isArray(value)) return value.join(", ");
  if (value == null) return "-";
  return String(value);
}

interface Props {
  item: RecommendationItem;
}

export default function EvidencePanel({ item }: Props) {
  const factorEntries = Object.entries(item.eligibility_factors).filter(
    ([, status]) => status !== "NOT_APPLICABLE"
  );
  const benefitEntries = item.benefit_info ? Object.entries(item.benefit_info) : [];

  return (
    <div className="space-y-4 text-sm">
      {factorEntries.length > 0 && (
        <div>
          <p className="mb-1 font-medium text-gray-700">조건별 판별 결과</p>
          <ul className="space-y-1 rounded border border-gray-100 bg-gray-50 p-3">
            {factorEntries.map(([factor, status]) => (
              <li key={factor} className="flex justify-between">
                <span className="text-gray-600">{FACTOR_LABELS[factor] ?? factor}</span>
                <span className={`font-medium ${FACTOR_STATUS_CLASS[status] ?? "text-gray-600"}`}>
                  {FACTOR_STATUS_LABELS[status] ?? status}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {benefitEntries.length > 0 && (
        <div>
          <p className="mb-1 font-medium text-gray-700">예상 혜택 및 안내</p>
          <ul className="space-y-1 rounded border border-gray-100 bg-gray-50 p-3">
            {benefitEntries.map(([key, value]) => (
              <li key={key}>
                <span className="text-gray-600">{BENEFIT_FIELD_LABELS[key] ?? key}: </span>
                <span className="font-medium text-gray-900">{formatBenefitValue(value)}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {item.application_end && (
        <p className="text-gray-600">
          신청기한: <span className="font-medium text-gray-900">{item.application_end}</span>
        </p>
      )}

      {item.official_url && (
        <p className="text-gray-600">
          공식 출처:{" "}
          <a href={item.official_url} target="_blank" rel="noreferrer" className="font-medium text-blue-600 underline">
            {item.official_url}
          </a>
        </p>
      )}

      <p className="rounded bg-yellow-50 p-3 text-xs text-yellow-800">
        본 결과는 입력하신 정보를 기준으로 한 사전 판단이며, 실제 신청 가능 여부는 신청기관을 통해
        다시 확인해야 합니다. 확인 필요로 표시된 조건은 시스템이 자동으로 판단하지 않았습니다.
      </p>
    </div>
  );
}
