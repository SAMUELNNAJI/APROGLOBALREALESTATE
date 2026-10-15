from django.contrib.auth import get_user_model
from django.contrib.staticfiles import finders
from django.test import TestCase
from django.urls import reverse

User = get_user_model()

SIGNUP_DATA = {
    "first_name": "Ada",
    "last_name": "Obi",
    "email": "Ada@Example.com",
    "phone": "+234 800 000 0000",
    "password1": "Tr0ub4dor&Tower9",
    "password2": "Tr0ub4dor&Tower9",
    "accept_terms": "on",
}


class SitePageTests(TestCase):
    def test_site_pages_render_with_shared_layout(self):
        for name in ("home", "index", "services", "listings", "about", "contact", "privacy", "terms"):
            with self.subTest(page=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, "base.html")
                self.assertContains(response, 'class="navbar"')
                self.assertContains(response, 'class="footer"')

    def test_unknown_page_returns_404(self):
        self.assertEqual(self.client.get("/not-a-page.html").status_code, 404)

    def test_static_assets_are_discoverable(self):
        for path in ("css/styles.css", "css/auth.css", "css/dashboard.css", "js/auth.js", "image/logo.png"):
            with self.subTest(path=path):
                self.assertIsNotNone(finders.find(path))

    def test_auth_pages_render(self):
        for name in ("signin", "signup"):
            with self.subTest(page=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, "base.html")


class AuthFlowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.purchaser = User.objects.create_user("buyer@example.com", "buyer@example.com", "Sup3r&Secret!pass")
        cls.boss = User.objects.create_superuser("boss", "boss@example.com", "Sup3r&Secret!pass")

    def test_signup_creates_purchaser_and_opens_purchaser_dashboard(self):
        response = self.client.post(reverse("signup"), SIGNUP_DATA)
        self.assertRedirects(response, reverse("purchaser_dashboard"))
        user = User.objects.get(email="ada@example.com")
        self.assertEqual(user.username, "ada@example.com")
        self.assertFalse(user.is_superuser)
        self.assertEqual(user.profile.phone, "+234 800 000 0000")
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    def test_signup_rejects_duplicate_email_and_weak_or_mismatched_passwords(self):
        bad = {**SIGNUP_DATA, "email": "BUYER@example.com"}
        self.assertContains(self.client.post(reverse("signup"), bad), "already exists")
        weak = {**SIGNUP_DATA, "password1": "12345678", "password2": "12345678"}
        self.assertFalse(self.client.post(reverse("signup"), weak).context["form"].is_valid())
        mismatch = {**SIGNUP_DATA, "password2": "different"}
        self.assertContains(self.client.post(reverse("signup"), mismatch), "don&#x27;t match")
        self.assertEqual(User.objects.count(), 2)

    def test_signup_requires_terms(self):
        data = {k: v for k, v in SIGNUP_DATA.items() if k != "accept_terms"}
        self.assertEqual(User.objects.filter(email="ada@example.com").count(), 0)
        self.assertContains(self.client.post(reverse("signup"), data), "accept the Terms")

    def test_purchaser_signin_goes_to_purchaser_dashboard(self):
        response = self.client.post(
            reverse("signin"), {"username": "buyer@example.com", "password": "Sup3r&Secret!pass"}
        )
        self.assertRedirects(response, reverse("purchaser_dashboard"))
        self.assertTemplateUsed(self.client.get(reverse("purchaser_dashboard")), "dashboard/Purchase Dashboard/index.html")

    def test_signin_accepts_email_case_insensitively(self):
        response = self.client.post(
            reverse("signin"), {"username": "BUYER@Example.com", "password": "Sup3r&Secret!pass"}
        )
        self.assertRedirects(response, reverse("purchaser_dashboard"))

    def test_superuser_signin_goes_to_apro_global_dashboard(self):
        response = self.client.post(
            reverse("signin"), {"username": "boss", "password": "Sup3r&Secret!pass"}
        )
        self.assertRedirects(response, reverse("apro_dashboard"))
        self.assertTemplateUsed(self.client.get(reverse("apro_dashboard")), "dashboard/Apro Global Dashboard/index.html")

    def test_superuser_can_also_sign_in_with_email(self):
        response = self.client.post(
            reverse("signin"), {"username": "boss@example.com", "password": "Sup3r&Secret!pass"}
        )
        self.assertRedirects(response, reverse("apro_dashboard"))

    def test_bad_credentials_show_error(self):
        response = self.client.post(reverse("signin"), {"username": "boss", "password": "nope"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "don&#x27;t match")

    def test_safe_next_is_honoured_but_external_next_is_not(self):
        data = {"username": "boss", "password": "Sup3r&Secret!pass"}
        response = self.client.post(reverse("signin"), {**data, "next": "/about.html"})
        self.assertRedirects(response, "/about.html")
        self.client.logout()
        response = self.client.post(reverse("signin"), {**data, "next": "https://evil.example/"})
        self.assertRedirects(response, reverse("apro_dashboard"))

    def test_dashboard_routes_by_role(self):
        self.assertEqual(self.client.get(reverse("dashboard")).status_code, 302)
        self.client.force_login(self.purchaser)
        self.assertRedirects(self.client.get(reverse("dashboard")), reverse("purchaser_dashboard"))
        self.client.force_login(self.boss)
        self.assertRedirects(self.client.get(reverse("dashboard")), reverse("apro_dashboard"))

    def test_dashboards_are_access_controlled(self):
        for name in ("purchaser_dashboard", "apro_dashboard"):
            response = self.client.get(reverse(name))
            self.assertRedirects(response, f"{reverse('signin')}?next={reverse(name)}")
        self.client.force_login(self.purchaser)
        self.assertRedirects(self.client.get(reverse("apro_dashboard")), reverse("purchaser_dashboard"))
        self.client.force_login(self.boss)
        self.assertRedirects(self.client.get(reverse("purchaser_dashboard")), reverse("apro_dashboard"))

    def test_authenticated_users_skip_auth_pages(self):
        self.client.force_login(self.purchaser)
        self.assertRedirects(self.client.get(reverse("signin")), reverse("purchaser_dashboard"))
        self.assertRedirects(self.client.get(reverse("signup")), reverse("purchaser_dashboard"))

    def test_apro_dashboard_lists_purchasers_only(self):
        self.client.force_login(self.boss)
        response = self.client.get(reverse("apro_dashboard"))
        self.assertEqual(response.context["total_purchasers"], 1)
        self.assertContains(response, "buyer@example.com")

    def test_signout_requires_post_and_logs_out(self):
        self.client.force_login(self.purchaser)
        self.assertEqual(self.client.get(reverse("signout")).status_code, 405)
        self.assertRedirects(self.client.post(reverse("signout")), reverse("home"))
        self.assertNotIn("_auth_user_id", self.client.session)
