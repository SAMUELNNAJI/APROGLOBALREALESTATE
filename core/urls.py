from django.contrib.auth.views import LogoutView
from django.urls import path
from django.views.generic import TemplateView

from . import views

urlpatterns = [
    # ── Health check (used by Render; no database access) ──
    path("healthz", views.healthz, name="healthz"),

    # ── Static / template pages ──────────────
    path("",             views.home_view,                          name="home"),
    path("index.html",   views.home_view,                          name="index"),
    path("services.html",TemplateView.as_view(template_name="services.html"), name="services"),
    path("about.html",   TemplateView.as_view(template_name="about.html"),    name="about"),
    path("contact.html", TemplateView.as_view(template_name="contact.html"),  name="contact"),
    path("privacy.html", TemplateView.as_view(template_name="privacy.html"),  name="privacy"),
    path("terms.html",   TemplateView.as_view(template_name="terms.html"),    name="terms"),

    # ── Dynamic pages ────────────────────────
    path("listings.html",       views.listings_view,        name="listings"),
    path("listings/",           views.listings_view,        name="listings_clean"),
    path("property/<slug:slug>/", views.property_detail_view, name="property_detail"),
    path("blog/",               views.blog_view,            name="blog"),
    path("blog/<slug:slug>/",   views.blog_detail_view,     name="blog_detail"),
    path("search/",             views.hero_search,          name="hero_search"),

    # ── Auth ─────────────────────────────────
    path("signin/",  views.SignInView.as_view(), name="signin"),
    path("signup/",  views.SignUpView.as_view(), name="signup"),
    path("signout/", LogoutView.as_view(),       name="signout"),

    # ── Dashboard router ─────────────────────
    path("dashboard/", views.dashboard, name="dashboard"),

    # ── Purchaser dashboard ──────────────────
    path("dashboard/my/",            views.purchaser_dashboard, name="purchaser_dashboard"),
    path("property/<slug:slug>/save/", views.toggle_save_property, name="toggle_save_property"),
    path("book/<slug:slug>/",        views.book_inspection,     name="book_inspection"),
    path("booking/<str:ref>/pay/",   views.inspection_payment,  name="inspection_payment"),


    # ── Support Live Chat ──────────────────────
    path("support/tickets/",     views.support_tickets,    name="support_tickets"),
    path("support/ticket/new/",  views.support_create,     name="support_create"),
    path("support/ticket/<int:pk>/chat/",   views.support_chat,      name="support_chat"),
    path("support/ticket/<int:pk>/messages/", views.support_messages, name="support_messages"),
    path("support/ticket/<int:pk>/send/",     views.support_send,    name="support_send"),
    path("support/ticket/<int:pk>/assign/",   views.support_assign,  name="support_assign"),


    # ── Admin dashboard ──────────────────────
    path("dashboard/admin/",                      views.apro_dashboard,               name="apro_dashboard"),
    path("dashboard/admin/properties/",           views.admin_properties,             name="admin_properties"),
    path("dashboard/admin/properties/add/",       views.admin_property_create,        name="admin_property_create"),
    path("dashboard/admin/properties/<int:pk>/edit/",   views.admin_property_edit,   name="admin_property_edit"),
    path("dashboard/admin/properties/<int:pk>/delete/", views.admin_property_delete, name="admin_property_delete"),
    path("dashboard/admin/blog/",                 views.admin_blog,                   name="admin_blog"),
    path("dashboard/admin/blog/add/",             views.admin_blog_create,            name="admin_blog_create"),
    path("dashboard/admin/blog/<int:pk>/edit/",   views.admin_blog_edit,              name="admin_blog_edit"),
    path("dashboard/admin/blog/<int:pk>/delete/", views.admin_blog_delete,            name="admin_blog_delete"),
    path("dashboard/admin/bookings/",             views.admin_bookings,               name="admin_bookings"),
    path("dashboard/admin/bookings/<int:pk>/status/", views.admin_booking_update_status, name="admin_booking_status"),
    path("dashboard/admin/purchasers/",           views.admin_purchasers,             name="admin_purchasers"),
    path("dashboard/admin/analytics-data/",       views.admin_analytics_data,         name="admin_analytics_data"),
    path("dashboard/admin/bank/",                 views.admin_bank_details,           name="admin_bank_details"),
    path("dashboard/admin/bank/<int:pk>/delete/",views.admin_bank_delete,             name="admin_bank_delete"),
]
