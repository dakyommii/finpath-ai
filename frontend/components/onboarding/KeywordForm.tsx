"use client";

import { useState } from "react";
import { KEYWORD_TAXONOMY } from "@/types/finpath";
import type { InterestKeywordInput, KeywordAxis } from "@/types/finpath";

interface Props {
  initialData: InterestKeywordInput[];
  onBack: () => void;
  onSubmit: (data: InterestKeywordInput[]) => void;
}

function keyToken(item: InterestKeywordInput) {
  return `${item.axis}::${item.keyword}`;
}

export default function KeywordForm({ initialData, onBack, onSubmit }: Props) {
  const [selected, setSelected] = useState<InterestKeywordInput[]>(initialData);

  function toggle(axis: KeywordAxis, keyword: string) {
    setSelected((prev) => {
      const token = keyToken({ axis, keyword });
      const exists = prev.some((item) => keyToken(item) === token);
      if (exists) {
        return prev.filter((item) => keyToken(item) !== token);
      }
      return [...prev, { axis, keyword }];
    });
  }

  function isSelected(axis: KeywordAxis, keyword: string) {
    return selected.some((item) => item.axis === axis && item.keyword === keyword);
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-base font-semibold">관심사 키워드 (선택)</h2>
        <p className="mt-1 text-sm text-gray-500">
          해당되는 항목을 자유롭게 선택해주세요. 추천 결과가 조금 더 상황에 맞게 조정됩니다.
        </p>
      </div>

      {(Object.entries(KEYWORD_TAXONOMY) as [KeywordAxis, (typeof KEYWORD_TAXONOMY)[KeywordAxis]][]).map(
        ([axis, { label, keywords }]) => (
          <div key={axis}>
            <p className="mb-2 text-sm font-medium text-gray-700">{label}</p>
            <div className="flex flex-wrap gap-2">
              {keywords.map((keyword) => {
                const active = isSelected(axis, keyword);
                return (
                  <button
                    key={keyword}
                    type="button"
                    aria-pressed={active}
                    onClick={() => toggle(axis, keyword)}
                    className={`rounded-full border px-3 py-1.5 text-sm focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 ${
                      active
                        ? "border-blue-600 bg-blue-600 text-white"
                        : "border-gray-300 bg-white text-gray-700 hover:bg-gray-50"
                    }`}
                  >
                    {keyword}
                  </button>
                );
              })}
            </div>
          </div>
        )
      )}

      <div className="flex gap-3">
        <button
          type="button"
          onClick={onBack}
          className="flex-1 rounded border py-2 font-semibold focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600"
        >
          이전
        </button>
        <button
          type="button"
          onClick={() => onSubmit(selected)}
          className="flex-1 rounded bg-blue-600 py-2 font-semibold text-white hover:bg-blue-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600"
        >
          다음
        </button>
      </div>
    </div>
  );
}
