from datetime import datetime, timezone

from app.models.learning_models import TaskAccuracySnapshot

ACCURACY_THRESHOLD = 90.0


async def record_feedback_accuracy(tenant_id: str, task_type: str, signal: int) -> TaskAccuracySnapshot:
    snap = await TaskAccuracySnapshot.find_one(
        TaskAccuracySnapshot.tenant_id == tenant_id,
        TaskAccuracySnapshot.task_type == task_type,
    )
    if not snap:
        snap = TaskAccuracySnapshot(tenant_id=tenant_id, task_type=task_type)
    if signal > 0:
        snap.positive_count += 1
    elif signal < 0:
        snap.negative_count += 1
    total = snap.positive_count + snap.negative_count
    snap.accuracy_pct = round((snap.positive_count / total) * 100, 1) if total else 100.0
    snap.updated_at = datetime.now(timezone.utc)
    if snap.id:
        await snap.save()
    else:
        await snap.insert()

    if snap.accuracy_pct < ACCURACY_THRESHOLD and snap.negative_count >= 3:
        from app.services.prompt_improvement_service import enqueue_task_improvement

        await enqueue_task_improvement(tenant_id, task_type)

    return snap


async def get_accuracy_summary(tenant_id: str) -> list[dict]:
    snaps = await TaskAccuracySnapshot.find(TaskAccuracySnapshot.tenant_id == tenant_id).to_list()
    return [s.to_dict() for s in snaps]
