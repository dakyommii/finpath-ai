from models import Roadmap, RoadmapStep
from services.roadmap_service import current_stage_and_progress


def save_roadmap(db, user_id, goal_id, steps) -> Roadmap:
    current_stage, progress = current_stage_and_progress(steps)
    estimated_completion_date = steps[-1].expected_end if steps else None

    roadmap = Roadmap(
        user_id=user_id,
        goal_id=goal_id,
        current_stage=current_stage,
        progress=progress,
        estimated_completion_date=estimated_completion_date,
    )
    db.add(roadmap)
    db.flush()

    for step in steps:
        db.add(
            RoadmapStep(
                roadmap_id=roadmap.id,
                step_order=step.order,
                title=step.title,
                status=step.status,
                recommended_start=step.recommended_start,
                expected_end=step.expected_end,
                action=step.action,
                reason=step.reason,
                completion_condition=step.completion_condition,
                related_items=step.related_items,
                sources=step.sources,
            )
        )

    db.commit()
    db.refresh(roadmap)
    return roadmap
