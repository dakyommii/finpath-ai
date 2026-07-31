"use client";

import { useState } from "react";
import ProfileForm from "./ProfileForm";
import GoalForm from "./GoalForm";
import LifeEventForm from "./LifeEventForm";
import { createGoal, createLifeEvent, createProfile, generateRecommendations, generateRoadmap } from "@/lib/api";
import type { DiagnosisData, GoalFormData, LifeEventFormData, ProfileInput } from "@/types/finpath";

type Step = "profile" | "goal" | "lifeEvent";

interface Props {
  onComplete: (data: DiagnosisData) => void;
}

const STEP_LABELS: { key: Step; label: string }[] = [
  { key: "profile", label: "기본정보 · 소득/자산 · 주거/부채" },
  { key: "goal", label: "금융 목표" },
  { key: "lifeEvent", label: "미래 이벤트" },
];

export default function OnboardingWizard({ onComplete }: Props) {
  const [step, setStep] = useState<Step>("profile");
  const [profileData, setProfileData] = useState<ProfileInput | null>(null);
  const [goalData, setGoalData] = useState<GoalFormData | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const currentIndex = STEP_LABELS.findIndex((s) => s.key === step);

  async function handleLifeEventSubmit(lifeEvent: LifeEventFormData | null) {
    if (!profileData || !goalData) return;
    setSubmitting(true);
    setError(null);
    try {
      const profile = await createProfile(profileData);
      const userId = profile.user_id;
      await createGoal(userId, goalData);
      if (lifeEvent) {
        await createLifeEvent(userId, lifeEvent);
      }
      const [roadmap, recommendations] = await Promise.all([
        generateRoadmap(userId),
        generateRecommendations(userId),
      ]);
      onComplete({ profile: profileData, goal: goalData, roadmap, recommendations });
    } catch (e) {
      setError(e instanceof Error ? e.message : "알 수 없는 오류가 발생했습니다.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-xl p-6">
      <ol className="mb-8 flex justify-between text-xs text-gray-500 sm:text-sm">
        {STEP_LABELS.map((s, i) => (
          <li key={s.key} className={i === currentIndex ? "font-semibold text-blue-600" : ""}>
            {i + 1}. {s.label}
          </li>
        ))}
      </ol>

      {error && <p className="mb-4 rounded bg-red-50 p-3 text-sm text-red-600">{error}</p>}

      {step === "profile" && (
        <ProfileForm
          initialData={profileData}
          onSubmit={(data) => {
            setProfileData(data);
            setStep("goal");
          }}
        />
      )}
      {step === "goal" && (
        <GoalForm
          initialData={goalData}
          onBack={() => setStep("profile")}
          onSubmit={(data) => {
            setGoalData(data);
            setStep("lifeEvent");
          }}
        />
      )}
      {step === "lifeEvent" && (
        <LifeEventForm
          onBack={() => setStep("goal")}
          onSubmit={handleLifeEventSubmit}
          submitting={submitting}
        />
      )}
    </div>
  );
}
