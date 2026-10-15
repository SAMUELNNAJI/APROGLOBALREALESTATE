from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password
from django.core.validators import RegexValidator

from .models import BankDetails, BlogPost, PaymentProof, InspectionBooking, Profile, Property

User = get_user_model()

phone_validator = RegexValidator(
    r"^\+?[0-9 ()-]{7,20}$", "Enter a valid phone number."
)


# ─────────────────────────────────────────────
# Auth forms (existing)
# ─────────────────────────────────────────────
class SignInForm(AuthenticationForm):
    username = forms.CharField(
        label="Email or username",
        widget=forms.TextInput(
            attrs={"autocomplete": "username", "placeholder": "you@example.com", "autofocus": True}
        ),
    )
    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(
            attrs={"autocomplete": "current-password", "placeholder": "Your password"}
        ),
    )
    remember_me = forms.BooleanField(required=False, label="Keep me signed in")

    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": "That email/username and password don't match. Please try again.",
    }

    def clean(self):
        username = self.cleaned_data.get("username")
        if username and "@" in username:
            match = User.objects.filter(email__iexact=username).first()
            if match:
                self.cleaned_data["username"] = match.get_username()
        return super().clean()


class SignUpForm(forms.ModelForm):
    phone = forms.CharField(
        max_length=20,
        validators=[phone_validator],
        widget=forms.TextInput(attrs={"autocomplete": "tel", "placeholder": "+234 800 000 0000"}),
    )
    password1 = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(
            attrs={"autocomplete": "new-password", "placeholder": "Create a strong password", "data-strength": True}
        ),
    )
    password2 = forms.CharField(
        label="Confirm password",
        strip=False,
        widget=forms.PasswordInput(
            attrs={"autocomplete": "new-password", "placeholder": "Repeat your password"}
        ),
    )
    accept_terms = forms.BooleanField(
        error_messages={"required": "You need to accept the Terms and Privacy Policy."}
    )

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")
        widgets = {
            "first_name": forms.TextInput(attrs={"autocomplete": "given-name", "placeholder": "First name"}),
            "last_name":  forms.TextInput(attrs={"autocomplete": "family-name", "placeholder": "Last name"}),
            "email":      forms.EmailInput(attrs={"autocomplete": "email", "placeholder": "you@example.com"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ("first_name", "last_name", "email"):
            self.fields[name].required = True

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists() or User.objects.filter(
            username__iexact=email
        ).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password1")
        p2 = cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "The two passwords don't match.")
        elif p1:
            candidate = User(
                username=cleaned.get("email", ""),
                email=cleaned.get("email", ""),
                first_name=cleaned.get("first_name", ""),
                last_name=cleaned.get("last_name", ""),
            )
            try:
                validate_password(p1, candidate)
            except forms.ValidationError as error:
                self.add_error("password1", error)
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data["email"]
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
            Profile.objects.create(user=user, phone=self.cleaned_data["phone"])
        return user


# ─────────────────────────────────────────────
# Property form (admin upload)
# ─────────────────────────────────────────────
class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        fields = [
            "title", "status", "property_type", "city", "location",
            "price", "price_label", "booking_fee", "bedrooms", "bathrooms", "size_sqm",
            "description", "image", "image_url", "is_featured", "is_active",
        ]
        widgets = {
            "title":        forms.TextInput(attrs={"placeholder": "e.g. 3 Bedroom Flat – Lekki Phase 1"}),
            "location":     forms.TextInput(attrs={"placeholder": "e.g. Lekki Phase 1, Lagos"}),
            "price":        forms.NumberInput(attrs={"placeholder": "e.g. 85000000"}),
            "price_label":  forms.TextInput(attrs={"placeholder": "sale / year / plot"}),
            "booking_fee":  forms.NumberInput(attrs={"placeholder": "e.g. 5000", "step": "0.01", "min": "0"}),
            "description":  forms.Textarea(attrs={"rows": 5, "placeholder": "Property description…"}),
            "image_url":    forms.URLInput(attrs={"placeholder": "https://…"}),
        }


# ─────────────────────────────────────────────
# BlogPost form (admin)
# ─────────────────────────────────────────────
class BlogPostForm(forms.ModelForm):
    class Meta:
        model = BlogPost
        fields = [
            "title", "category", "excerpt", "content",
            "image", "image_url", "author", "is_featured", "is_published",
        ]
        widgets = {
            "title":    forms.TextInput(attrs={"placeholder": "Post title…"}),
            "excerpt":  forms.Textarea(attrs={"rows": 3, "placeholder": "Short excerpt (max 300 chars)…"}),
            "content":  forms.Textarea(attrs={"rows": 12, "placeholder": "Full article content…"}),
            "image_url": forms.URLInput(attrs={"placeholder": "https://…"}),
            "author":   forms.TextInput(attrs={"placeholder": "Apro Global Team"}),
        }


# ─────────────────────────────────────────────
# Bank Details form (admin)
# ─────────────────────────────────────────────
class BankDetailsForm(forms.ModelForm):
    class Meta:
        model = BankDetails
        fields = ["bank_name", "account_name", "account_number", "is_active"]
        widgets = {
            "bank_name":      forms.TextInput(attrs={"placeholder": "e.g. First Bank Nigeria"}),
            "account_name":   forms.TextInput(attrs={"placeholder": "Apro Global Real Estate Ltd"}),
            "account_number": forms.TextInput(attrs={"placeholder": "1234567890"}),
        }


# ─────────────────────────────────────────────
# Inspection Booking form (purchaser)
# ─────────────────────────────────────────────
class InspectionBookingForm(forms.ModelForm):
    class Meta:
        model = InspectionBooking
        fields = ["full_name", "email", "phone", "preferred_date", "preferred_time", "message"]
        widgets = {
            "full_name":      forms.TextInput(attrs={"placeholder": "Your full name"}),
            "email":          forms.EmailInput(attrs={"placeholder": "you@example.com"}),
            "phone":          forms.TextInput(attrs={"placeholder": "+234 800 000 0000"}),
            "preferred_date": forms.DateInput(attrs={"type": "date"}),
            "preferred_time": forms.TimeInput(attrs={"type": "time"}),
            "message":        forms.Textarea(attrs={"rows": 3, "placeholder": "Any additional notes…"}),
        }


# ─────────────────────────────────────────────
# Payment Proof form (purchaser)
# ─────────────────────────────────────────────
class PaymentProofForm(forms.ModelForm):
    class Meta:
        model = PaymentProof
        fields = ["amount_paid", "proof_image"]
        widgets = {
            "amount_paid": forms.NumberInput(attrs={"placeholder": "Amount paid (₦)"}),
        }


User = get_user_model()

phone_validator = RegexValidator(
    r"^\+?[0-9 ()-]{7,20}$", "Enter a valid phone number."
)


class SignInForm(AuthenticationForm):
    username = forms.CharField(
        label="Email or username",
        widget=forms.TextInput(
            attrs={"autocomplete": "username", "placeholder": "you@example.com", "autofocus": True}
        ),
    )
    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(
            attrs={"autocomplete": "current-password", "placeholder": "Your password"}
        ),
    )
    remember_me = forms.BooleanField(required=False, label="Keep me signed in")

    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": "That email/username and password don't match. Please try again.",
    }

    def clean(self):
        username = self.cleaned_data.get("username")
        if username and "@" in username:
            match = User.objects.filter(email__iexact=username).first()
            if match:
                self.cleaned_data["username"] = match.get_username()
        return super().clean()


class SignUpForm(forms.ModelForm):
    phone = forms.CharField(
        max_length=20,
        validators=[phone_validator],
        widget=forms.TextInput(attrs={"autocomplete": "tel", "placeholder": "+234 800 000 0000"}),
    )
    password1 = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(
            attrs={"autocomplete": "new-password", "placeholder": "Create a strong password", "data-strength": True}
        ),
    )
    password2 = forms.CharField(
        label="Confirm password",
        strip=False,
        widget=forms.PasswordInput(
            attrs={"autocomplete": "new-password", "placeholder": "Repeat your password"}
        ),
    )
    accept_terms = forms.BooleanField(
        error_messages={"required": "You need to accept the Terms and Privacy Policy."}
    )

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")
        widgets = {
            "first_name": forms.TextInput(attrs={"autocomplete": "given-name", "placeholder": "First name"}),
            "last_name": forms.TextInput(attrs={"autocomplete": "family-name", "placeholder": "Last name"}),
            "email": forms.EmailInput(attrs={"autocomplete": "email", "placeholder": "you@example.com"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ("first_name", "last_name", "email"):
            self.fields[name].required = True

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists() or User.objects.filter(
            username__iexact=email
        ).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean(self):
        cleaned = super().clean()
        password1 = cleaned.get("password1")
        password2 = cleaned.get("password2")
        if password1 and password2 and password1 != password2:
            self.add_error("password2", "The two passwords don't match.")
        elif password1:
            candidate = User(
                username=cleaned.get("email", ""),
                email=cleaned.get("email", ""),
                first_name=cleaned.get("first_name", ""),
                last_name=cleaned.get("last_name", ""),
            )
            try:
                validate_password(password1, candidate)
            except forms.ValidationError as error:
                self.add_error("password1", error)
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data["email"]
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
            Profile.objects.create(user=user, phone=self.cleaned_data["phone"])
        return user
