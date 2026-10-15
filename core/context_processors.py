"""Global dashboard context (sidebar badges, etc)."""
from .models import ChatMessage, SupportTicket


def _admin_unread_total():
    total = 0
    tickets = SupportTicket.objects.only("id", "purchaser_id", "admin_read_at")
    for ticket in tickets:
        qs = ChatMessage.objects.filter(
            ticket_id=ticket.pk, sender_id=ticket.purchaser_id
        )
        if ticket.admin_read_at is not None:
            qs = qs.filter(created_at__gt=ticket.admin_read_at)
        total += qs.count()
        if total > 99:
            break
    return total


def _purchaser_unread_total(user):
    ticket = (
        SupportTicket.objects.filter(purchaser=user)
        .order_by("-updated_at")
        .only("id", "purchaser_read_at")
        .first()
    )
    if ticket is None:
        return 0
    qs = ChatMessage.objects.filter(ticket_id=ticket.pk).exclude(
        sender_id=user.pk
    )
    if ticket.purchaser_read_at is not None:
        qs = qs.filter(created_at__gt=ticket.purchaser_read_at)
    return qs.count()


def support_unread(request):
    """Expose ``support_unread_total`` to every dashboard page for the sidebar badge."""
    user = getattr(request, "user", None)
    if user is None or not getattr(user, "is_authenticated", False):
        return {}
    try:
        if user.is_superuser:
            return {"support_unread_total": _admin_unread_total()}
        return {"support_unread_total": _purchaser_unread_total(user)}
    except Exception:
        return {"support_unread_total": 0}
