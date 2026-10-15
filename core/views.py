import json
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import Http404, JsonResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import FormView

from .forms import (
    BankDetailsForm,
    BlogPostForm,
    InspectionBookingForm,
    PaymentProofForm,
    PropertyForm,
    SignInForm,
    SignUpForm,
)
from .models import (
    BankDetails,
    BlogPost,
    ChatMessage,
    InspectionBooking,
    PaymentProof,
    Property,
    SavedProperty,
    SupportTicket,
)

User = get_user_model()


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
def is_admin(user):
    return user.is_superuser


def dashboard_url_for(user):
    return reverse("apro_dashboard" if user.is_superuser else "purchaser_dashboard")


def saved_property_ids(user):
    """Return a set of Property IDs the given user has saved (wishlisted)."""
    if not user.is_authenticated:
        return set()
    return set(
        SavedProperty.objects.filter(user=user).values_list("property_id", flat=True)
    )


# ─────────────────────────────────────────────
# Auth
# ─────────────────────────────────────────────
class SignInView(LoginView):
    template_name = "auth/signin.html"
    authentication_form = SignInForm
    redirect_authenticated_user = True

    def get_default_redirect_url(self):
        return dashboard_url_for(self.request.user)

    def form_valid(self, form):
        response = super().form_valid(form)
        if not form.cleaned_data.get("remember_me"):
            self.request.session.set_expiry(0)
        return response


class SignUpView(FormView):
    template_name = "auth/signup.html"
    form_class = SignUpForm
    success_url = reverse_lazy("purchaser_dashboard")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(dashboard_url_for(request.user))
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return super().form_valid(form)


@login_required
def dashboard(request):
    return redirect(dashboard_url_for(request.user))


# ─────────────────────────────────────────────
# Public pages
# ─────────────────────────────────────────────
def home_view(request):
    """Home page — featured properties and latest blog posts from the database."""
    featured_properties = (
        Property.objects.filter(is_active=True)
        .order_by("-is_featured", "-created_at")[:6]
    )
    featured_post = (
        BlogPost.objects.filter(is_published=True, is_featured=True)
        .order_by("-published_at")
        .first()
    )
    latest_posts = BlogPost.objects.filter(is_published=True).order_by("-published_at")[:5]
    return render(request, "index.html", {
        "featured_properties": featured_properties,
        "featured_post": featured_post,
        "latest_posts": latest_posts,
        "saved_ids": saved_property_ids(request.user),
    })


def listings_view(request):
    """Listings page with filtering, search, pagination."""
    qs = Property.objects.filter(is_active=True)

    # ── tab filter (sale / rent)
    tab = request.GET.get("tab", "all")
    if tab in ("sale", "rent"):
        qs = qs.filter(status=tab)
    elif tab == "new":
        qs = qs.filter(status="new")

    # ── dropdowns
    location = request.GET.get("location", "all")
    if location in ("lagos", "abuja"):
        qs = qs.filter(city=location)

    prop_type = request.GET.get("type", "all")
    if prop_type != "all":
        qs = qs.filter(property_type=prop_type)

    price_range = request.GET.get("price", "all")
    if price_range == "low":
        qs = qs.filter(price__lt=10_000_000)
    elif price_range == "mid":
        qs = qs.filter(price__gte=10_000_000, price__lte=100_000_000)
    elif price_range == "high":
        qs = qs.filter(price__gt=100_000_000)

    # ── sort
    sort = request.GET.get("sort", "default")
    if sort == "price-asc":
        qs = qs.order_by("price")
    elif sort == "price-desc":
        qs = qs.order_by("-price")
    else:
        qs = qs.order_by("-created_at")

    # ── hero search query forwarded from home
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(
            Q(title__icontains=q) | Q(location__icontains=q) | Q(description__icontains=q)
        )

    total = qs.count()
    paginator = Paginator(qs, 9)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "page_obj":    page_obj,
        "total":       total,
        "tab":         tab,
        "location":    location,
        "prop_type":   prop_type,
        "price_range": price_range,
        "sort":        sort,
        "q":           q,
        "saved_ids":   saved_property_ids(request.user),
    }
    return render(request, "listings.html", context)


def blog_view(request):
    """Blog listing with pagination."""
    qs = BlogPost.objects.filter(is_published=True)
    paginator = Paginator(qs, 6)
    page_obj = paginator.get_page(request.GET.get("page"))
    featured = qs.filter(is_featured=True).first()
    context = {"page_obj": page_obj, "featured": featured}
    return render(request, "blog/index.html", context)


def blog_detail_view(request, slug):
    post = get_object_or_404(BlogPost, slug=slug, is_published=True)
    # Prefer same-category posts, then top up with the latest others so the
    # "Related Articles" row always looks full (up to 3).
    same_category = list(
        BlogPost.objects.filter(is_published=True, category=post.category)
        .exclude(pk=post.pk)
        .order_by("-published_at")[:3]
    )
    related = same_category
    if len(related) < 3:
        exclude_pks = [post.pk] + [r.pk for r in related]
        filler = list(
            BlogPost.objects.filter(is_published=True)
            .exclude(pk__in=exclude_pks)
            .order_by("-published_at")[: 3 - len(related)]
        )
        related = related + filler
    sidebar_properties = (
        Property.objects.filter(is_active=True)
        .order_by("-is_featured", "-created_at")[:4]
    )
    return render(request, "blog/detail.html", {
        "post": post,
        "related": related,
        "sidebar_properties": sidebar_properties,
    })


def property_detail_view(request, slug):
    prop = get_object_or_404(Property, slug=slug, is_active=True)
    bank = BankDetails.objects.filter(is_active=True).first()
    is_saved = (
        request.user.is_authenticated
        and SavedProperty.objects.filter(user=request.user, property=prop).exists()
    )
    return render(request, "property_detail.html", {
        "prop": prop,
        "bank": bank,
        "is_saved": is_saved,
    })


def hero_search(request):
    """Redirect hero search form → listings page with params."""
    params = {}
    tab = request.GET.get("tab", "all")
    if tab != "all":
        params["tab"] = tab
    loc = request.GET.get("location", "")
    if loc and loc != "all":
        params["location"] = loc
    ptype = request.GET.get("property_type", "")
    if ptype and ptype != "all":
        params["type"] = ptype
    price = request.GET.get("price_range", "")
    if price and price != "all":
        params["price"] = price
    rooms = request.GET.get("rooms", "")
    if rooms:
        params["q"] = rooms  # fallback: search by rooms text
    # build query string
    from urllib.parse import urlencode
    qs = urlencode(params)
    return redirect(f"{reverse('listings')}?{qs}")


# ─────────────────────────────────────────────
# Purchaser Dashboard
# ─────────────────────────────────────────────
@login_required
def purchaser_dashboard(request):
    if request.user.is_superuser:
        return redirect("apro_dashboard")
    bookings = InspectionBooking.objects.filter(purchaser=request.user).select_related("property")
    saved = (
        SavedProperty.objects.filter(user=request.user)
        .select_related("property")
        .order_by("-saved_at")
    )
    context = {
        "bookings": bookings,
        "bookings_count": bookings.count(),
        "pending_count": bookings.filter(status="pending").count(),
        "confirmed_count": bookings.filter(status="confirmed").count(),
        "saved_properties": saved,
        "saved_count": saved.count(),
    }
    return render(request, "dashboard/Purchase Dashboard/index.html", context)


@login_required
def toggle_save_property(request, slug):
    """AJAX endpoint — add/remove a property from the purchaser's wishlist.

    Admins are not allowed to save. Returns JSON: {saved: bool, count: int}.
    """
    if not request.method == "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    # Admins manage the platform — they don't have a wishlist.
    if request.user.is_superuser:
        return JsonResponse(
            {"error": "Admins can't save properties.", "admin": True}, status=403
        )

    prop = get_object_or_404(Property, slug=slug, is_active=True)
    existing = SavedProperty.objects.filter(user=request.user, property=prop).first()
    if existing:
        existing.delete()
        saved = False
    else:
        SavedProperty.objects.create(user=request.user, property=prop)
        saved = True

    count = SavedProperty.objects.filter(user=request.user).count()
    return JsonResponse({"saved": saved, "count": count})


@login_required
def book_inspection(request, slug):
    """Step 1 — fill booking form. Admins are not allowed."""
    if request.user.is_superuser:
        # Return a flag so the property detail page can show the modal
        prop = get_object_or_404(Property, slug=slug, is_active=True)
        bank = BankDetails.objects.filter(is_active=True).first()
        return render(request, "property_detail.html", {
            "prop": prop,
            "bank": bank,
            "admin_booking_blocked": True,
        })
    prop = get_object_or_404(Property, slug=slug, is_active=True)
    bank = BankDetails.objects.filter(is_active=True).first()
    if request.method == "POST":
        form = InspectionBookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.purchaser = request.user
            booking.property = prop
            booking.save()
            return redirect("inspection_payment", ref=booking.reference)
    else:
        # pre-fill from user profile
        form = InspectionBookingForm(initial={
            "full_name": request.user.get_full_name(),
            "email":     request.user.email,
            "phone":     getattr(getattr(request.user, "profile", None), "phone", ""),
        })
    return render(request, "booking/book.html", {"form": form, "prop": prop, "bank": bank})


@login_required
def inspection_payment(request, ref):
    """Step 2 — show ATM card + upload proof."""
    booking = get_object_or_404(
        InspectionBooking.objects.select_related("property"),
        reference=ref, purchaser=request.user,
    )
    fee = booking.property.booking_fee
    bank    = BankDetails.objects.filter(is_active=True).first()
    already = PaymentProof.objects.filter(booking=booking).exists()

    if request.method == "POST" and not already:
        form = PaymentProofForm(request.POST, request.FILES)
        if form.is_valid():
            proof = form.save(commit=False)
            proof.booking = booking
            proof.save()
            booking.status = "paid"
            booking.save()
            messages.success(request, "Payment proof submitted! We'll verify and confirm your inspection.")
            return redirect("purchaser_dashboard")
    else:
        form = PaymentProofForm(initial={"amount_paid": fee})

    return render(request, "booking/payment.html", {
        "booking": booking,
        "bank":    bank,
        "form":    form,
        "already": already,
    })


# ─────────────────────────────────────────────
# Admin Dashboard
# ─────────────────────────────────────────────
@login_required
def apro_dashboard(request):
    if not is_admin(request.user):
        # Mirror purchaser_dashboard: role mismatches go to the other
        # dashboard instead of the sign-in page.
        return redirect("purchaser_dashboard")
    purchasers = User.objects.filter(is_superuser=False)
    week_ago   = timezone.now() - timedelta(days=7)
    bookings   = InspectionBooking.objects.select_related("purchaser", "property")
    context = {
        "total_purchasers":  purchasers.count(),
        "new_this_week":     purchasers.filter(date_joined__gte=week_ago).count(),
        "active_accounts":   purchasers.filter(is_active=True).count(),
        "admin_count":       User.objects.filter(is_superuser=True).count(),
        "recent_purchasers": purchasers.select_related("profile").order_by("-date_joined")[:8],
        "total_properties":  Property.objects.count(),
        "total_posts":       BlogPost.objects.count(),
        "pending_bookings":  bookings.filter(status="pending").count(),
        "paid_bookings":     bookings.filter(status="paid").count(),
    }
    return render(request, "dashboard/Apro Global Dashboard/index.html", context)


# ── Purchasers ──────────────────────────────
@login_required
@user_passes_test(is_admin, login_url="signin")
def admin_purchasers(request):
    """All registered purchaser users (non-superusers), paginated."""
    purchasers_qs = (
        User.objects.filter(is_superuser=False)
        .select_related("profile")
        .order_by("-date_joined")
    )
    paginator = Paginator(purchasers_qs, 10)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "dashboard/Apro Global Dashboard/purchasers.html",
                  {"purchasers": page_obj, "page_obj": page_obj})


# ── Dashboard analytics (live JSON for the graph) ──
@login_required
@user_passes_test(is_admin, login_url="signin")
def admin_analytics_data(request):
    """Return bookings-per-day for the last 14 days as JSON (for the live chart)."""
    days = 14
    today = timezone.localdate()
    start = today - timedelta(days=days - 1)

    # Count bookings grouped by day
    rows = (
        InspectionBooking.objects.filter(created_at__date__gte=start)
        .extra(select={"day": "date(created_at)"})
        .values("day")
        .annotate(total=Count("id"))
    )
    counts = {r["day"]: r["total"] for r in rows}

    labels, data = [], []
    for i in range(days):
        d = start + timedelta(days=i)
        key = d.isoformat()
        labels.append(d.strftime("%d %b"))
        data.append(counts.get(key, 0))

    return JsonResponse({"labels": labels, "data": data})


# ── Properties ───────────────────────────────
@login_required
@user_passes_test(is_admin, login_url="signin")
def admin_properties(request):
    paginator = Paginator(Property.objects.all(), 9)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "dashboard/Apro Global Dashboard/properties.html",
                  {"props": page_obj, "page_obj": page_obj})


@login_required
@user_passes_test(is_admin, login_url="signin")
def admin_property_create(request):
    form = PropertyForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Property added successfully.")
        return redirect("admin_properties")
    return render(request, "dashboard/Apro Global Dashboard/property_form.html",
                  {"form": form, "action": "Add"})


@login_required
@user_passes_test(is_admin, login_url="signin")
def admin_property_edit(request, pk):
    prop = get_object_or_404(Property, pk=pk)
    form = PropertyForm(request.POST or None, request.FILES or None, instance=prop)
    if form.is_valid():
        form.save()
        messages.success(request, "Property updated.")
        return redirect("admin_properties")
    return render(request, "dashboard/Apro Global Dashboard/property_form.html",
                  {"form": form, "action": "Edit", "prop": prop})


@login_required
@user_passes_test(is_admin, login_url="signin")
def admin_property_delete(request, pk):
    prop = get_object_or_404(Property, pk=pk)
    if request.method == "POST":
        prop.delete()
        messages.success(request, "Property deleted.")
    return redirect("admin_properties")


# ── Blog ─────────────────────────────────────
@login_required
@user_passes_test(is_admin, login_url="signin")
def admin_blog(request):
    paginator = Paginator(BlogPost.objects.all(), 6)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "dashboard/Apro Global Dashboard/blog.html",
                  {"posts": page_obj, "page_obj": page_obj})


@login_required
@user_passes_test(is_admin, login_url="signin")
def admin_blog_create(request):
    form = BlogPostForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Blog post published.")
        return redirect("admin_blog")
    return render(request, "dashboard/Apro Global Dashboard/blog_form.html",
                  {"form": form, "action": "Add"})


@login_required
@user_passes_test(is_admin, login_url="signin")
def admin_blog_edit(request, pk):
    post = get_object_or_404(BlogPost, pk=pk)
    form = BlogPostForm(request.POST or None, request.FILES or None, instance=post)
    if form.is_valid():
        form.save()
        messages.success(request, "Post updated.")
        return redirect("admin_blog")
    return render(request, "dashboard/Apro Global Dashboard/blog_form.html",
                  {"form": form, "action": "Edit", "post": post})


@login_required
@user_passes_test(is_admin, login_url="signin")
def admin_blog_delete(request, pk):
    post = get_object_or_404(BlogPost, pk=pk)
    if request.method == "POST":
        post.delete()
        messages.success(request, "Post deleted.")
    return redirect("admin_blog")


# ── Bookings ─────────────────────────────────
@login_required
@user_passes_test(is_admin, login_url="signin")
def admin_bookings(request):
    bookings_qs = InspectionBooking.objects.select_related(
        "purchaser", "property", "payment"
    ).order_by("-created_at")
    paginator = Paginator(bookings_qs, 10)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "dashboard/Apro Global Dashboard/bookings.html",
                  {"bookings": page_obj, "page_obj": page_obj})


@login_required
@user_passes_test(is_admin, login_url="signin")
def admin_booking_update_status(request, pk):
    booking = get_object_or_404(InspectionBooking, pk=pk)
    if request.method == "POST":
        new_status = request.POST.get("status")
        if new_status in dict(InspectionBooking.STATUS_CHOICES):
            booking.status = new_status
            booking.save()
            messages.success(request, f"Booking {booking.reference} updated to {booking.get_status_display()}.")
    return redirect("admin_bookings")


# ── Bank Details ─────────────────────────────
@login_required
@user_passes_test(is_admin, login_url="signin")
def admin_bank_details(request):
    details = BankDetails.objects.all()
    form    = BankDetailsForm()
    if request.method == "POST":
        form = BankDetailsForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Bank details saved.")
            return redirect("admin_bank_details")
    return render(request, "dashboard/Apro Global Dashboard/bank_details.html",
                  {"details": details, "form": form})


@login_required
@user_passes_test(is_admin, login_url="signin")
def admin_bank_delete(request, pk):
    bd = get_object_or_404(BankDetails, pk=pk)
    if request.method == "POST":
        bd.delete()
        messages.success(request, "Bank details removed.")
    return redirect("admin_bank_details")

# ─────────────────────────────────────────────
# Support Live Chat
# ─────────────────────────────────────────────
def _purchaser_conversation(user):
    """Return the purchaser's single WhatsApp-style conversation (auto-created).

    There is no "open a ticket" step — every purchaser simply has one chat
    with the support team, the moment they open the page.
    """
    conv = SupportTicket.objects.filter(purchaser=user).order_by("-updated_at").first()
    if conv is None:
        conv = SupportTicket.objects.create(purchaser=user, subject="Support Chat")
    return conv


def _render_chat(request, active):
    """Shared renderer for the WhatsApp-style chat page."""
    context = {
        "active": active,
        "chat_messages": (
            active.messages.select_related("sender").order_by("created_at")
            if active is not None
            else ChatMessage.objects.none()
        ),
    }
    if request.user.is_superuser:
        context["conversations"] = list(
            SupportTicket.objects.select_related("purchaser")
            .prefetch_related("messages")
            .order_by("-updated_at")
        )
    return render(request, "chat/chat.html", context)


@login_required
def support_tickets(request):
    """WhatsApp-style support chat.

    Purchasers land directly inside their own conversation. Admins get a
    conversation list on the left plus the open chat pane on the right.
    """
    if request.user.is_superuser:
        active = None
        wanted = request.GET.get("t", "")
        if wanted.isdigit():
            active = SupportTicket.objects.filter(pk=int(wanted)).first()
        if active is None:
            active = SupportTicket.objects.order_by("-updated_at").first()
        return _render_chat(request, active)
    return _render_chat(request, _purchaser_conversation(request.user))


@login_required
def support_create(request):
    if request.method == "POST":
        SupportTicket.objects.create(purchaser=request.user, subject=request.POST.get("subject", "").strip())
        return JsonResponse({"ok": True})


@login_required
def support_assign(request, pk):
    if not request.user.is_superuser:
        return HttpResponseForbidden()
    ticket = get_object_or_404(SupportTicket, pk=pk)
    ticket.assigned_admin = request.user
    ticket.status = "open"
    ticket.save()
    return JsonResponse({"ok": True, "status": ticket.status, "ticket_id": ticket.pk})


@login_required
def support_chat(request, pk):
    """Direct link into one conversation (admins pick it up in the list pane)."""
    ticket = get_object_or_404(SupportTicket, pk=pk)
    if not request.user.is_superuser and ticket.purchaser != request.user:
        raise Http404
    return _render_chat(request, ticket)


@login_required
def support_messages(request, pk):
    ticket = get_object_or_404(SupportTicket, pk=pk)
    if not request.user.is_superuser and ticket.purchaser != request.user:
        return HttpResponseForbidden()
    messages = ticket.messages.select_related("sender").order_by("-created_at")[:60]
    data = [
        {
            "id": m.id,
            "sender": m.sender.username,
            "content": m.content,
            "created_at": m.created_at.isoformat(),
            "is_admin": m.sender.is_superuser,
        }
        for m in messages
    ]
    return JsonResponse({"messages": data})


@login_required
def support_send(request, pk):
    if request.method == "POST":
        ticket = get_object_or_404(SupportTicket, pk=pk)
        if not request.user.is_superuser and ticket.purchaser != request.user:
            return HttpResponseForbidden()
        content = request.POST.get("content", "").strip()
        if not content:
            return JsonResponse({"ok": False, "error": "Message cannot be empty."}, status=400)
        message = ChatMessage.objects.create(ticket=ticket, sender=request.user, content=content)
        # Bump activity so the admin's conversation list re-orders live
        SupportTicket.objects.filter(pk=ticket.pk).update(updated_at=timezone.now())
        return JsonResponse({
            "ok": True,
            "id": message.id,
            "sender": message.sender.username,
            "content": message.content,
            "created_at": message.created_at.isoformat(),
            "is_admin": message.sender.is_superuser,
        })



# ─────────────────────────────────────────────
# Health check
# ─────────────────────────────────────────────
def healthz(request):
    """Liveness endpoint for Render health checks (does not touch the DB)."""
    return JsonResponse({"status": "ok"})

