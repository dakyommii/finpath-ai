from dataclasses import dataclass
from datetime import date
from types import SimpleNamespace
from typing import Optional

from services.roadmap_service import generate_roadmap_steps

PROFILE_FIELDS = [
    "age", "region", "job_status", "annual_income", "marital_status",
    "housing_type", "liquid_assets", "total_debt", "monthly_saving", "credit_score_band",
]


def _clone_profile_with_overrides(profile, monthly_saving=None, annual_income=None) -> SimpleNamespace:
    """SQLAlchemy 프로필 객체를 건드리지 않고, 필요한 필드만 복사한 뒤 변경값을 덮어써
    시뮬레이션 전용 프로필을 만든다."""
    data = {field: getattr(profile, field) for field in PROFILE_FIELDS}
    if monthly_saving is not None:
        data["monthly_saving"] = monthly_saving
    if annual_income is not None:
        data["annual_income"] = annual_income
    return SimpleNamespace(**data)


def _months_between(later: date, earlier: date) -> int:
    return (later.year - earlier.year) * 12 + (later.month - earlier.month)


@dataclass
class SimulationStepSummary:
    title: str
    status: str
    recommended_start: Optional[date]
    expected_end: Optional[date]


@dataclass
class SimulationResult:
    original_estimated_completion_date: Optional[date]
    simulated_estimated_completion_date: Optional[date]
    months_saved: Optional[int]
    added_steps: list[str]
    removed_steps: list[str]
    original_steps: list[SimulationStepSummary]
    simulated_steps: list[SimulationStepSummary]


def simulate_roadmap(db, roadmap, profile, goals, life_events, monthly_saving=None,
                      annual_income=None, extra_life_events=None) -> SimulationResult:
    """10.2/10.3: 조건 변경 전(현재 저장된 로드맵)과 변경 후(재계산)를 비교한다.

    변경 후 로드맵은 DB에 저장하지 않는다 — 사용자가 실제로 조건을 반영하고 싶으면
    /api/v1/roadmaps/generate를 다시 호출해 정식으로 재생성한다.
    """
    sim_profile = _clone_profile_with_overrides(profile, monthly_saving, annual_income)
    sim_life_events = list(life_events) + list(extra_life_events or [])

    simulated_steps = generate_roadmap_steps(db, sim_profile, goals, sim_life_events)

    original_titles = [s.title for s in roadmap.steps]
    simulated_titles = [s.title for s in simulated_steps]
    added_steps = [t for t in simulated_titles if t not in original_titles]
    removed_steps = [t for t in original_titles if t not in simulated_titles]

    original_end = roadmap.estimated_completion_date
    simulated_end = simulated_steps[-1].expected_end if simulated_steps else None
    months_saved = (
        _months_between(original_end, simulated_end)
        if original_end and simulated_end
        else None
    )

    return SimulationResult(
        original_estimated_completion_date=original_end,
        simulated_estimated_completion_date=simulated_end,
        months_saved=months_saved,
        added_steps=added_steps,
        removed_steps=removed_steps,
        original_steps=[
            SimulationStepSummary(s.title, s.status, s.recommended_start, s.expected_end)
            for s in roadmap.steps
        ],
        simulated_steps=[
            SimulationStepSummary(s.title, s.status, s.recommended_start, s.expected_end)
            for s in simulated_steps
        ],
    )
