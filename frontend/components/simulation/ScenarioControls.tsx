"use client";

import { FormEvent, useState } from "react";
import type { SimulationRequest } from "@/types/finpath";

interface Props {
  baselineMonthlySaving: number;
  baselineAnnualIncome: number;
  onSimulate: (input: SimulationRequest) => void;
  loading: boolean;
}

export default function ScenarioControls({ baselineMonthlySaving, baselineAnnualIncome, onSimulate, loading }: Props) {
  const [monthlySaving, setMonthlySaving] = useState(baselineMonthlySaving);
  const [annualIncome, setAnnualIncome] = useState(baselineAnnualIncome);
  const [marriagePlanned, setMarriagePlanned] = useState(false);

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const input: SimulationRequest = {
      monthly_saving: monthlySaving !== baselineMonthlySaving ? monthlySaving : undefined,
      annual_income: annualIncome !== baselineAnnualIncome ? annualIncome : undefined,
      life_events: marriagePlanned ? [{ event_type: "MARRIAGE" }] : undefined,
    };
    onSimulate(input);
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4 rounded-lg border border-gray-200 bg-white p-5">
      <h2 className="text-base font-semibold text-gray-900">조건 변경해보기</h2>

      <label className="block">
        <span className="text-sm text-gray-600">월 저축 가능액 (원)</span>
        <input
          type="number"
          className="mt-1 w-full rounded border border-gray-300 p-2 text-sm"
          value={monthlySaving}
          onChange={(e) => setMonthlySaving(Number(e.target.value))}
        />
      </label>

      <label className="block">
        <span className="text-sm text-gray-600">연 소득 (원)</span>
        <input
          type="number"
          className="mt-1 w-full rounded border border-gray-300 p-2 text-sm"
          value={annualIncome}
          onChange={(e) => setAnnualIncome(Number(e.target.value))}
        />
      </label>

      <label className="flex items-center gap-2">
        <input type="checkbox" checked={marriagePlanned} onChange={(e) => setMarriagePlanned(e.target.checked)} />
        <span className="text-sm text-gray-600">내년 결혼 예정</span>
      </label>

      <button
        type="submit"
        disabled={loading}
        className="w-full rounded bg-blue-600 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600"
      >
        {loading ? "계산 중..." : "시뮬레이션 실행"}
      </button>
    </form>
  );
}
