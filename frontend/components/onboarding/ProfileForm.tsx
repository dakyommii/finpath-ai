"use client";

import { FormEvent, useState } from "react";
import type { ProfileInput } from "@/types/finpath";

interface Props {
  initialData: ProfileInput | null;
  onSubmit: (data: ProfileInput) => void;
}

const JOB_STATUS_OPTIONS: { value: ProfileInput["job_status"]; label: string }[] = [
  { value: "EMPLOYED", label: "직장인" },
  { value: "SELF_EMPLOYED", label: "자영업자" },
  { value: "UNEMPLOYED", label: "미취업" },
  { value: "STUDENT", label: "학생" },
];

const MARITAL_STATUS_OPTIONS: { value: ProfileInput["marital_status"]; label: string }[] = [
  { value: "SINGLE", label: "미혼" },
  { value: "MARRIED", label: "기혼" },
  { value: "ENGAGED", label: "약혼" },
];

const HOUSING_TYPE_OPTIONS: { value: ProfileInput["housing_type"]; label: string }[] = [
  { value: "MONTHLY_RENT", label: "월세" },
  { value: "JEONSE", label: "전세" },
  { value: "OWN", label: "자가" },
];

const DEFAULT_FORM: ProfileInput = {
  age: 27,
  region: "서울",
  job_status: "EMPLOYED",
  annual_income: 38000000,
  marital_status: "SINGLE",
  housing_type: "MONTHLY_RENT",
  liquid_assets: 20000000,
  total_debt: 0,
  monthly_saving: 1000000,
  credit_score_band: "",
};

function fieldClass() {
  return "mt-1 w-full rounded border border-gray-300 p-2 text-sm";
}

export default function ProfileForm({ initialData, onSubmit }: Props) {
  const [form, setForm] = useState<ProfileInput>(initialData ?? DEFAULT_FORM);
  const [errors, setErrors] = useState<string[]>([]);

  function update<K extends keyof ProfileInput>(key: K, value: ProfileInput[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  function validate(): string[] {
    const errs: string[] = [];
    if (!form.age || form.age <= 0 || form.age > 120) errs.push("나이를 올바르게 입력해주세요.");
    if (!form.region.trim()) errs.push("거주지역을 입력해주세요.");
    if (form.annual_income < 0) errs.push("연 소득은 0 이상이어야 합니다.");
    if (form.liquid_assets < 0) errs.push("현금성 자산은 0 이상이어야 합니다.");
    if (form.monthly_saving < 0) errs.push("월 저축 가능액은 0 이상이어야 합니다.");
    if (form.total_debt != null && form.total_debt < 0) errs.push("총부채는 0 이상이어야 합니다.");
    return errs;
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const errs = validate();
    setErrors(errs);
    if (errs.length === 0) onSubmit(form);
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-8">
      {errors.length > 0 && (
        <ul className="rounded bg-red-50 p-3 text-sm text-red-600">
          {errors.map((err) => (
            <li key={err}>{err}</li>
          ))}
        </ul>
      )}

      <section>
        <h2 className="mb-3 text-base font-semibold">기본정보</h2>
        <div className="grid grid-cols-2 gap-4">
          <label className="block">
            <span className="text-sm text-gray-600">나이</span>
            <input
              type="number"
              className={fieldClass()}
              value={form.age}
              onChange={(e) => update("age", Number(e.target.value))}
              required
            />
          </label>
          <label className="block">
            <span className="text-sm text-gray-600">거주지역</span>
            <input
              type="text"
              className={fieldClass()}
              value={form.region}
              onChange={(e) => update("region", e.target.value)}
              required
            />
          </label>
          <label className="block">
            <span className="text-sm text-gray-600">직업 상태</span>
            <select
              className={fieldClass()}
              value={form.job_status}
              onChange={(e) => update("job_status", e.target.value as ProfileInput["job_status"])}
            >
              {JOB_STATUS_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </label>
        </div>
      </section>

      <section>
        <h2 className="mb-3 text-base font-semibold">소득 및 자산</h2>
        <div className="grid grid-cols-2 gap-4">
          <label className="block">
            <span className="text-sm text-gray-600">연 소득 (원)</span>
            <input
              type="number"
              className={fieldClass()}
              value={form.annual_income}
              onChange={(e) => update("annual_income", Number(e.target.value))}
              required
            />
          </label>
          <label className="block">
            <span className="text-sm text-gray-600">현금성 자산 (원)</span>
            <input
              type="number"
              className={fieldClass()}
              value={form.liquid_assets}
              onChange={(e) => update("liquid_assets", Number(e.target.value))}
              required
            />
          </label>
          <label className="block">
            <span className="text-sm text-gray-600">신용점수 구간 (선택)</span>
            <input
              type="text"
              className={fieldClass()}
              value={form.credit_score_band ?? ""}
              onChange={(e) => update("credit_score_band", e.target.value)}
            />
          </label>
        </div>
      </section>

      <section>
        <h2 className="mb-3 text-base font-semibold">주거 및 부채</h2>
        <div className="grid grid-cols-2 gap-4">
          <label className="block">
            <span className="text-sm text-gray-600">혼인 여부</span>
            <select
              className={fieldClass()}
              value={form.marital_status}
              onChange={(e) => update("marital_status", e.target.value as ProfileInput["marital_status"])}
            >
              {MARITAL_STATUS_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </label>
          <label className="block">
            <span className="text-sm text-gray-600">주거형태</span>
            <select
              className={fieldClass()}
              value={form.housing_type}
              onChange={(e) => update("housing_type", e.target.value as ProfileInput["housing_type"])}
            >
              {HOUSING_TYPE_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </label>
          <label className="block">
            <span className="text-sm text-gray-600">총부채 (원, 선택)</span>
            <input
              type="number"
              className={fieldClass()}
              value={form.total_debt ?? 0}
              onChange={(e) => update("total_debt", Number(e.target.value))}
            />
          </label>
          <label className="block">
            <span className="text-sm text-gray-600">월 저축 가능액 (원)</span>
            <input
              type="number"
              className={fieldClass()}
              value={form.monthly_saving}
              onChange={(e) => update("monthly_saving", Number(e.target.value))}
              required
            />
          </label>
        </div>
      </section>

      <button
        type="submit"
        className="w-full rounded bg-blue-600 py-2 font-semibold text-white hover:bg-blue-700"
      >
        다음
      </button>
    </form>
  );
}
