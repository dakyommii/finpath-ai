"use client";

import { FormEvent, useState } from "react";
import type { LifeEventFormData } from "@/types/finpath";

interface Props {
  onBack: () => void;
  onSubmit: (data: LifeEventFormData | null) => void;
  submitting: boolean;
}

const EVENT_TYPE_OPTIONS: { value: LifeEventFormData["event_type"]; label: string }[] = [
  { value: "MARRIAGE", label: "결혼" },
  { value: "CHILDBIRTH", label: "출산" },
  { value: "RELOCATION", label: "이사" },
  { value: "JOB_CHANGE", label: "이직" },
];

const CERTAINTY_OPTIONS = ["확정", "예상", "관심"];

export default function LifeEventForm({ onBack, onSubmit, submitting }: Props) {
  const [enabled, setEnabled] = useState(false);
  const [form, setForm] = useState<LifeEventFormData>({
    event_type: "MARRIAGE",
    expected_date: undefined,
    certainty: "예상",
  });

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    onSubmit(enabled ? form : null);
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <h2 className="text-base font-semibold">미래 이벤트 (선택)</h2>

      <label className="flex items-center gap-2">
        <input type="checkbox" checked={enabled} onChange={(e) => setEnabled(e.target.checked)} />
        <span className="text-sm text-gray-600">결혼, 이사, 출산 등 예정된 이벤트가 있어요</span>
      </label>

      {enabled && (
        <div className="space-y-4">
          <label className="block">
            <span className="text-sm text-gray-600">이벤트 유형</span>
            <select
              className="mt-1 w-full rounded border border-gray-300 p-2 text-sm"
              value={form.event_type}
              onChange={(e) =>
                setForm((p) => ({ ...p, event_type: e.target.value as LifeEventFormData["event_type"] }))
              }
            >
              {EVENT_TYPE_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </label>
          <label className="block">
            <span className="text-sm text-gray-600">예상 시점</span>
            <input
              type="date"
              className="mt-1 w-full rounded border border-gray-300 p-2 text-sm"
              value={form.expected_date ?? ""}
              onChange={(e) => setForm((p) => ({ ...p, expected_date: e.target.value || undefined }))}
            />
          </label>
          <label className="block">
            <span className="text-sm text-gray-600">확실성</span>
            <select
              className="mt-1 w-full rounded border border-gray-300 p-2 text-sm"
              value={form.certainty}
              onChange={(e) => setForm((p) => ({ ...p, certainty: e.target.value }))}
            >
              {CERTAINTY_OPTIONS.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </label>
        </div>
      )}

      <div className="flex gap-3">
        <button type="button" onClick={onBack} className="flex-1 rounded border py-2 font-semibold" disabled={submitting}>
          이전
        </button>
        <button
          type="submit"
          disabled={submitting}
          className="flex-1 rounded bg-blue-600 py-2 font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {submitting ? "생성 중..." : "로드맵 생성하기"}
        </button>
      </div>
    </form>
  );
}
