# -*- coding: utf-8 -*-
"""Temporary smoke test for the WhatsApp-style chat enhancements. Deleted after run."""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
src = open("manage.py", encoding="utf-8").read()
mod = re.search(r"DJANGO_SETTINGS_MODULE\"\s*,\s*['\"]([^'\"]+)['\"]", src).group(1)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", mod)
import django
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from core.models import SupportTicket, ChatMessage

U = get_user_model()
PASS = []
def ok(name, cond, extra=""):
    if not cond:
        raise AssertionError("FAIL: %s %s" % (name, extra))
    PASS.append(name)
    print("PASS:", name)

# ── setup (idempotent) ──────────────────────────────────────────
U.objects.filter(username__startswith="smoke_admin_").delete()
U.objects.filter(username__startswith="smoke_buyer").delete()
admin = U.objects.create_user("smoke_admin_1", password="pw", is_superuser=True, is_staff=True)
buyer = U.objects.create_user("smoke_buyer1", password="pw")
buyer2 = U.objects.create_user("smoke_buyer2", password="pw")

cb = Client(); cb.force_login(buyer)
cb2 = Client(); cb2.force_login(buyer2)
ca = Client(); ca.force_login(admin)

try:
    # ── buyer1 opens chat (auto-creates conversation) + sends 2 msgs ──
    r = cb.get("/support/tickets/")
    ok("buyer page renders", r.status_code == 200)
    t1 = SupportTicket.objects.get(purchaser=buyer)
    for txt in ("Hello from buyer one", "Need help with a booking"):
        resp = cb.post("/support/ticket/%d/send/" % t1.pk, {"content": txt})
        ok("buyer send ok", resp.json().get("ok") is True)

    # ── buyer2: second conversation with 2 unread-for-admin msgs ──
    t2 = SupportTicket.objects.create(purchaser=buyer2, subject="Support Chat")
    for txt in ("Hi, buyer two here", "Question about my payment"):
        resp = cb2.post("/support/ticket/%d/send/" % t2.pk, {"content": txt})
        ok("buyer2 send ok", resp.json().get("ok") is True)

    # ── admin list page: badges for BOTH conversations, include renders ──
    r = ca.get("/support/tickets/")
    html = r.content.decode()
    ok("admin page renders", r.status_code == 200)
    ok("2 badges on admin list", html.count('class="wa-badge"') == 2,
       "got %d" % html.count('class="wa-badge"'))
    ok("badge counts are 2", '>2<' in html)
    ok("pane include rendered (messageList)", 'id="messageList"' in html)
    ok("no show-chat without ?t=", 'class="wa-page"' in html and 'wa-page show-chat' not in html)
    ok("no ChatMessage str leak", "Chat message #" not in html)
    ok("back button present for admin", 'class="wa-back"' in html)
    ok("data-id on convo links", 'data-id="%d"' % t1.pk in html and 'data-id="%d"' % t2.pk in html)

    # ── open t1 via ?t= → badge for t1 cleared, t2 keeps its badge ──
    r = ca.get("/support/tickets/?t=%d" % t1.pk)
    html = r.content.decode()
    ok("?t= page renders", r.status_code == 200)
    ok("show-chat set with ?t=", 'class="wa-page show-chat"' in html)
    ok("only t2 badge remains", html.count('class="wa-badge"') == 1,
       "got %d" % html.count('class="wa-badge"'))
    t1.refresh_from_db()
    ok("admin_read_at stamped on ?t= open", t1.admin_read_at is not None)
    ok("pane shows t1", 'data-ticket="%d"' % t1.pk in html)

    # ── sidebar JSON reflects unread counts per ticket ──
    data = ca.get("/support/sidebar/").json()["sidebar"]
    by_id = {d["id"]: d for d in data}
    ok("sidebar has 2 convos", len(data) == 2)
    ok("t1 unread=0 after open", by_id[t1.pk]["unread"] == 0)
    ok("t2 unread=2", by_id[t2.pk]["unread"] == 2)
    ok("sidebar preview text", by_id[t2.pk]["preview"] == "Question about my payment")

    # ── new buyer message → badge appears; polling marks read → clears ──
    cb.post("/support/ticket/%d/send/" % t1.pk, {"content": "one more thing"})
    data = ca.get("/support/sidebar/").json()["sidebar"]
    by_id = {d["id"]: d for d in data}
    ok("t1 unread=1 after new msg", by_id[t1.pk]["unread"] == 1)
    r = ca.get("/support/ticket/%d/messages/" % t1.pk)
    ok("messages poll ok", r.status_code == 200 and len(r.json()["messages"]) >= 3)
    data = ca.get("/support/sidebar/").json()["sidebar"]
    by_id = {d["id"]: d for d in data}
    ok("t1 unread=0 after poll (read)", by_id[t1.pk]["unread"] == 0)

    # ── mark-read must NOT bump updated_at (list order stays stable) ──
    t1.refresh_from_db()
    before = t1.updated_at
    ca.get("/support/ticket/%d/messages/" % t1.pk)
    t1.refresh_from_db()
    ok("updated_at untouched by read", t1.updated_at == before)

    # ── pane fragment endpoint ──
    r = ca.get("/support/ticket/%d/pane/" % t1.pk)
    pt = r.content.decode()
    ok("pane fragment renders", r.status_code == 200)
    ok("fragment is a wa-pane", 'class="wa-pane"' in pt)
    ok("fragment has data-ticket + data-last", 'data-ticket="%d"' % t1.pk in pt and "data-last=" in pt)
    ok("fragment has back button", 'class="wa-back"' in pt)
    r2 = cb.get("/support/ticket/%d/pane/" % t1.pk)
    ok("buyer pane fragment ok", r2.status_code == 200 and 'class="wa-back"' not in r2.content.decode())
    r3 = cb2.get("/support/ticket/%d/pane/" % t1.pk)
    ok("foreign buyer gets 404 on pane", r3.status_code == 404)

    # ── permissions ──
    ok("buyer sidebar forbidden", cb.get("/support/sidebar/").status_code == 403)
    ok("anon redirected to login", Client().get("/support/sidebar/").status_code == 302)

    # ── deep-link poll marks read + direct url boots into chat ──
    ca.get("/support/ticket/%d/messages/" % t2.pk)
    t2.refresh_from_db()
    ok("deep-link poll marks t2 read", t2.admin_read_at is not None)
    r = ca.get("/support/ticket/%d/chat/" % t2.pk)
    ok("direct chat url show-chat", b"wa-page show-chat" in r.content)

    # ── purchaser page: no sidebar, full-page chat, str leak free ──
    ph = cb.get("/support/tickets/").content.decode()
    ok("buyer show-chat full page", 'class="wa-page show-chat"' in ph)
    ok("buyer has no convo sidebar", '<aside class="wa-list">' not in ph)
    ok("buyer no back button", 'class="wa-back"' not in ph)
    ok("buyer no str leak", "Chat message #" not in ph)

    # ── __str__ hardened ──
    m = ChatMessage.objects.filter(ticket=t1).first()
    ok("__str__ hardens", str(m) == "Chat message #%d" % m.pk, repr(str(m)))

    # ── extract rendered chat JS for node --check ──
    js_blocks = re.findall(r"<script>(.*?)</script>", html, re.S)
    chat_js = next(b for b in js_blocks if "function openChat" in b)
    open("__chat_js.js", "w", encoding="utf-8").write(chat_js)
    ok("chat JS extracted for syntax check", len(chat_js) > 3000)
    print("\nALL %d CHECKS PASSED" % len(PASS))
finally:
    U.objects.filter(username__startswith="smoke_admin_").delete()
    U.objects.filter(username__startswith="smoke_buyer").delete()
    print("cleanup done")
