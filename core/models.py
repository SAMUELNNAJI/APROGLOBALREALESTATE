from django.conf import settings
from django.db import models
from django.utils.text import slugify
import uuid


# ─────────────────────────────────────────────
# Profile (existing)
# ─────────────────────────────────────────────
class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    phone = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Profile for {self.user}"


# ─────────────────────────────────────────────
# Property Listing
# ─────────────────────────────────────────────
class Property(models.Model):
    STATUS_CHOICES = [
        ("sale", "For Sale"),
        ("rent", "For Rent"),
        ("new",  "New"),
    ]
    PROPERTY_TYPE_CHOICES = [
        ("apartment", "Apartment / Flat"),
        ("duplex",    "Duplex"),
        ("townhouse", "Townhouse"),
        ("office",    "Office"),
        ("land",      "Land"),
        ("house",     "Detached House"),
    ]
    CITY_CHOICES = [
        ("lagos", "Lagos"),
        ("abuja", "Abuja"),
    ]

    title         = models.CharField(max_length=200)
    slug          = models.SlugField(max_length=220, unique=True, blank=True)
    status        = models.CharField(max_length=20, choices=STATUS_CHOICES, default="sale")
    property_type = models.CharField(max_length=40, choices=PROPERTY_TYPE_CHOICES, default="apartment")
    city          = models.CharField(max_length=20, choices=CITY_CHOICES, default="lagos")
    location      = models.CharField(max_length=200)  # e.g. "Lekki Phase 1, Lagos"
    price         = models.DecimalField(max_digits=14, decimal_places=2)
    price_label   = models.CharField(max_length=40, default="sale",
                                     help_text="e.g. 'sale', 'year', 'plot'")
    booking_fee   = models.DecimalField(max_digits=12, decimal_places=2, default=5000,
                                        help_text="Booking / Inspection fee — amount a purchaser pays to book this property")
    bedrooms      = models.PositiveSmallIntegerField(default=0)
    bathrooms     = models.PositiveSmallIntegerField(default=0)
    size_sqm      = models.PositiveIntegerField(default=0)
    description   = models.TextField(blank=True)
    image         = models.ImageField(upload_to="properties/", blank=True, null=True)
    image_url     = models.URLField(blank=True, help_text="Fallback external image URL")
    is_featured   = models.BooleanField(default=False)
    is_active     = models.BooleanField(default=True)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Properties"

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)
            slug = base
            n = 1
            while Property.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{n}"
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_image(self):
        if self.image:
            return self.image.url
        return self.image_url or ""

    def formatted_price(self):
        p = int(self.price)
        if p >= 1_000_000:
            return f"₦{p / 1_000_000:.0f}M" if p % 1_000_000 == 0 else f"₦{p / 1_000_000:.1f}M"
        if p >= 1_000:
            return f"₦{p / 1_000:.0f}K"
        return f"₦{p:,}"

    def formatted_booking_fee(self):
        return f"₦{int(self.booking_fee):,}"




# ─────────────────────────────────────────────
# Blog Post
# ─────────────────────────────────────────────
class BlogPost(models.Model):
    CATEGORY_CHOICES = [
        ("market",     "Market Trends"),
        ("buyer",      "Buyer's Guide"),
        ("abuja",      "Abuja"),
        ("lagos",      "Lagos"),
        ("commercial", "Commercial"),
        ("management", "Property Management"),
        ("investment", "Investment"),
        ("finance",    "Finance"),
        ("legal",      "Legal"),
    ]

    title       = models.CharField(max_length=220)
    slug        = models.SlugField(max_length=240, unique=True, blank=True)
    category    = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default="market")
    excerpt     = models.TextField(max_length=300)
    content     = models.TextField()
    image       = models.ImageField(upload_to="blog/", blank=True, null=True)
    image_url   = models.URLField(blank=True)
    author      = models.CharField(max_length=100, default="Apro Global Team")
    is_featured = models.BooleanField(default=False)
    is_published = models.BooleanField(default=True)
    published_at = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-published_at"]

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)
            slug = base
            n = 1
            while BlogPost.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{n}"
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_image(self):
        if self.image:
            return self.image.url
        return self.image_url or ""


# ─────────────────────────────────────────────
# Bank Details (admin-configurable, ATM card)
# ─────────────────────────────────────────────
class BankDetails(models.Model):
    bank_name      = models.CharField(max_length=100)
    account_name   = models.CharField(max_length=200)
    account_number = models.CharField(max_length=20)
    is_active      = models.BooleanField(default=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Bank Details"

    def __str__(self):
        return f"{self.bank_name} — {self.account_number}"


# ─────────────────────────────────────────────
# Inspection Booking
# ─────────────────────────────────────────────
class InspectionBooking(models.Model):
    STATUS_CHOICES = [
        ("pending",  "Pending Payment"),
        ("paid",     "Payment Submitted"),
        ("verified", "Payment Verified"),
        ("rejected", "Payment Rejected"),
        ("confirmed","Inspection Confirmed"),
    ]

    reference      = models.CharField(max_length=20, unique=True, editable=False)
    purchaser      = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="bookings"
    )
    property       = models.ForeignKey(
        Property, on_delete=models.CASCADE, related_name="bookings"
    )
    full_name      = models.CharField(max_length=200)
    email          = models.EmailField()
    phone          = models.CharField(max_length=20)
    preferred_date = models.DateField()
    preferred_time = models.TimeField()
    message        = models.TextField(blank=True)
    status         = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = f"APG{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.reference} — {self.property.title}"


# ─────────────────────────────────────────────
# Payment Proof
# ─────────────────────────────────────────────
class PaymentProof(models.Model):
    booking     = models.OneToOneField(
        InspectionBooking, on_delete=models.CASCADE, related_name="payment"
    )
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2)
    proof_image = models.ImageField(upload_to="payment_proofs/")
    submitted_at = models.DateTimeField(auto_now_add=True)
    admin_note  = models.TextField(blank=True)

    def __str__(self):
        return f"Proof for {self.booking.reference}"


# ─────────────────────────────────────────────
# Saved Property (purchaser wishlist)
# ─────────────────────────────────────────────
class SavedProperty(models.Model):
    user     = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="saved_properties"
    )
    property = models.ForeignKey(
        Property, on_delete=models.CASCADE,
        related_name="saves"
    )
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "property")
        ordering = ["-saved_at"]

    def __str__(self):
        return f"{self.user} saved {self.property}"

    # ─────────────────────────────────────────────
    # Support Tickets & Live Chat
    # ─────────────────────────────────────────────
class SupportTicket(models.Model):
    STATUS_CHOICES = [
        ("open", "Open"),
        ("closed", "Closed"),
    ]

    subject = models.CharField(max_length=200)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="open")
    purchaser = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="support_tickets",
    )
    assigned_admin = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="assigned_tickets",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.purchaser} — {self.subject[:40]}"

    @property
    def is_open(self):
        return self.status == "open"




class ChatMessage(models.Model):
    ticket = models.ForeignKey(
        SupportTicket, on_delete=models.CASCADE, related_name="messages",
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.sender} on {self.ticket} ({self.content[:30]!r})"

