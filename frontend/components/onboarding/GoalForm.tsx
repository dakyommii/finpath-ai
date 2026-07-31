"use client";

import { FormEvent, useState } from "react";
import type { GoalFormData } from "@/types/finpath";

interface Props {
  initialData: GoalFormData | null;
  onBack: () => void;
  onSubmit: (data: GoalFormData) => void;
}

const GOAL_TYPE_OPTIONS: { value: GoalFormData["goal_type"]; label: string }[] = [
  { value: "JEONSE", label: "전세 자금 마련" },
  { value: "HOME_PURCHASE", label: "주택 구입" },
  { value: "SEED_MONEY", label: "목돈 마련" },
  { value: "DEBT_REPAYMENT", label: "부채 상환" },
];

const DEFAULT_FORM: GoalFormData = {
  goal_type: "SEED_MONEY",
  target_amount: undefined,
  target_date: undefined,
  priority: 1,
};

export default function GoalForm({ initialData, onBack, onSubmit }: Props) {
  const [form, setForm] = useState<GoalFormData>(initialData ?? DEFAULT_FORM);
  const [error, setError] = useState<string | null>(null);

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (form.target_amount != null && form.target_amount < 0) {
      setError("목표금액은 0 이상이어야 합니다.");
      return;
    }
    setError(null);
    onSubmit(form);
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <h2 className="text-base font-semibold">금융 목표</h2>
      {error && <p className="rounded bg-red-50 p-3 text-sm text-red-600">{error}</p>}

      <label className="block">
        <span className="text-sm text-gray-600">목표 유형</span>
        <select
          className="mt-1 w-full rounded border border-gray-300 p-2 text-sm"
          value={form.goal_type}
          onChange={(e) => setForm((p) => ({ ...p, goal_type: e.target.value as GoalFormData["goal_type"] }))}
        >
          {GOAL_TYPE_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
      </label>

      <label className="block">
        <span className="text-sm text-gray-600">목표 금액 (원, 선택)</span>
        <input
          type="number"
          className="mt-1 w-full rounded border border-gray-300 p-2 text-sm"
          value={form.target_amount ?? ""}
          onChange={(e) =>
            setForm((p) => ({ ...p, target_amount: e.target.value ? Number(e.target.value) : undefined }))
          }
        />
      </label>

      <label className="block">
        <span className="text-sm text-gray-600">목표 시점 (선택)</span>
        <input
          type="date"
          className="mt-1 w-full rounded border border-gray-300 p-2 text-sm"
          value={form.target_date ?? ""}
          onChange={(e) => setForm((p) => ({ ...p, target_date: e.target.value || undefined }))}
        />
      </label>

      <div className="flex gap-3">
        <button type="button" onClick={onBack} className="flex-1 rounded border py-2 font-semibold">
          이전
        </button>
        <button
          type="submit"
          className="flex-1 rounded bg-blue-600 py-2 font-semibold text-white hover:bg-blue-700"
        >
          다음
        </button>
      </div>
    </form>
  );
}
