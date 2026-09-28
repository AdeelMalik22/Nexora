from .models import AuditLog


def record_event(*, shop, action, object_type, object_id, actor=None, request=None, before=None, after=None, reason=""):
    return AuditLog.objects.create(
        shop=shop,
        actor=actor,
        action=action,
        object_type=object_type,
        object_id=str(object_id),
        request_id=getattr(request, "request_id", "") if request else "",
        device_id=getattr(request, "device_id", "") if request else "",
        before=before,
        after=after,
        reason=reason,
    )
