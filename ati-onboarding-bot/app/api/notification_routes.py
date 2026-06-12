from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth.dependencies import get_current_user
from app.models.notification import Notification
from app.models.user import User

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("")
async def list_notifications(
    user: User = Depends(get_current_user),
    unread_only: bool = Query(False),
    limit: int = Query(30, ge=1, le=100),
):
    query = Notification.find(Notification.user_id == str(user.id))
    if unread_only:
        query = Notification.find(Notification.user_id == str(user.id), Notification.is_read == False)
    items = await query.sort(-Notification.created_at).limit(limit).to_list()
    unread = await Notification.find(
        Notification.user_id == str(user.id), Notification.is_read == False
    ).count()
    return {"notifications": [n.to_dict() for n in items], "unread_count": unread}


@router.patch("/{notification_id}/read")
async def mark_read(notification_id: str, user: User = Depends(get_current_user)):
    notif = await Notification.get(notification_id)
    if not notif or notif.user_id != str(user.id):
        raise HTTPException(status_code=404, detail="Notification not found")
    notif.is_read = True
    await notif.save()
    return {"notification": notif.to_dict()}


@router.post("/read-all")
async def mark_all_read(user: User = Depends(get_current_user)):
    unread = await Notification.find(
        Notification.user_id == str(user.id), Notification.is_read == False
    ).to_list()
    for n in unread:
        n.is_read = True
        await n.save()
    return {"message": "All marked read", "count": len(unread)}
