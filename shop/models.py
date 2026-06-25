from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.html import strip_tags
from django.utils.text import Truncator, slugify
from imagekit.models import ImageSpecField
from pilkit.processors import ResizeToFit
from tinymce.models import HTMLField

CURRENCY_SYMBOLS = {'USD': '$', 'GBP': '£', 'EUR': '€'}


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('shop:category', args=[self.slug])


class Item(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = 'available', 'Available'
        RESERVED = 'reserved', 'Reserved'
        SOLD = 'sold', 'Sold'

    class Condition(models.TextChoices):
        MINT = 'mint', 'Mint'
        EXCELLENT = 'excellent', 'Excellent'
        VERY_GOOD = 'very_good', 'Very good'
        GOOD = 'good', 'Good'
        FAIR = 'fair', 'Fair'
        POOR = 'poor', 'Poor'
        FOR_RESTORATION = 'for_restoration', 'For restoration'

    title = models.CharField(
        max_length=200,
        help_text="The name of the piece as it will appear on the website.",
    )
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField(
        blank=True,
        help_text="Describe the piece and its story — anything a buyer would "
                  "like to know. This shows on the item's page.",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='items',
        help_text="Choose a category. You can add new categories under "
                  "“Categories” on the main admin page.",
    )
    # Money is stored as Decimal, never float. Currency is recorded explicitly.
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Selling price, numbers only (for example 249.99).",
    )
    currency = models.CharField(
        max_length=3,
        default='USD',
        help_text="3-letter currency code. Leave as USD unless you price in "
                  "another currency.",
    )
    status = models.CharField(
        max_length=20,
        choices=Status,
        default=Status.AVAILABLE,
        help_text="“Available” = for sale. “Reserved” = on hold for someone. "
                  "“Sold” = sold — this is permanent and can't be undone.",
    )
    condition = models.CharField(
        max_length=20,
        choices=Condition,
        blank=True,
        help_text="Overall condition of the piece (optional).",
    )
    era = models.CharField(
        max_length=100,
        blank=True,
        help_text='Period or era, for example "Victorian", "Art Deco", or "1960s".',
    )
    dimensions = models.CharField(
        max_length=255,
        blank=True,
        help_text='Size of the piece, for example "H 90 × W 45 × D 30 cm".',
    )
    provenance = models.TextField(
        blank=True,
        help_text="Where it came from or its history, if known.",
    )
    featured = models.BooleanField(
        default=False,
        verbose_name="feature on homepage",
        help_text="Tick to highlight this item in the featured section.",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="date added",
    )
    sold_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="date sold",
        help_text="Filled in automatically when the item is marked sold.",
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['slug']),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('shop:item', args=[self.slug])

    @property
    def display_price(self):
        symbol = CURRENCY_SYMBOLS.get(self.currency)
        if symbol:
            return f'{symbol}{self.price:,.2f}'
        return f'{self.price:,.2f} {self.currency}'

    @property
    def is_available(self):
        return self.status == self.Status.AVAILABLE

    @property
    def is_reserved(self):
        return self.status == self.Status.RESERVED

    @property
    def is_sold(self):
        return self.status == self.Status.SOLD

    def _previous_status(self):
        """The status currently stored in the DB, or None for unsaved items."""
        if not self.pk:
            return None
        return (
            Item.objects.filter(pk=self.pk)
            .values_list('status', flat=True)
            .first()
        )

    def clean(self):
        # "Sold is permanent": surfaces a tidy field error in the admin form.
        if (
            self._previous_status() == self.Status.SOLD
            and self.status != self.Status.SOLD
        ):
            raise ValidationError(
                {'status': 'A sold item cannot be changed back — "sold" is permanent.'}
            )

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        # Backstop for the permanence rule on any direct save() (not just admin).
        if (
            self._previous_status() == self.Status.SOLD
            and self.status != self.Status.SOLD
        ):
            raise ValidationError(
                'A sold item cannot be changed back — "sold" is permanent.'
            )
        # Stamp sold_at the first time the item becomes sold.
        if self.status == self.Status.SOLD and self.sold_at is None:
            self.sold_at = timezone.now()
        super().save(*args, **kwargs)


class ItemImage(models.Model):
    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name='images',
    )
    # The full-resolution upload is the source of truth and must be backed up
    # (see MEDIA_ROOT note in settings). The owner uploads large phone photos.
    image = models.ImageField(
        upload_to='items/%Y/%m/',
        help_text="Upload a photo. Large phone photos are fine — small "
                  "versions for the website are made automatically.",
    )

    # Derived, on-the-fly thumbnails (django-imagekit). These are NOT database
    # columns and need no migration; files are generated on first access and
    # cached under MEDIA_ROOT/CACHE. Use in templates via, e.g.:
    #     <img src="{{ image.thumbnail.url }}" alt="{{ image.alt_text }}">
    # `upscale=False` leaves already-small images at their original size.
    thumbnail = ImageSpecField(
        source='image',
        processors=[ResizeToFit(500, 500, upscale=False)],
        format='JPEG',
        options={'quality': 80},
    )
    # Larger, bounded image for an item's detail page so we never serve the
    # multi-megabyte original directly.
    detail_image = ImageSpecField(
        source='image',
        processors=[ResizeToFit(1200, 1200, upscale=False)],
        format='JPEG',
        options={'quality': 85},
    )

    alt_text = models.CharField(
        max_length=200,
        blank=True,
        help_text="A few words describing the photo (helps search engines and "
                  "visually-impaired visitors). Optional.",
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name="display order",
        help_text="Lower numbers show first (0, 1, 2 …).",
    )

    class Meta:
        ordering = ['sort_order', 'id']

    def __str__(self):
        return f'Image for {self.item.title} (#{self.sort_order})'


class Inquiry(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField()
    message = models.TextField()
    item = models.ForeignKey(
        Item,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inquiries',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    handled = models.BooleanField(
        default=False,
        help_text='Tick once you have responded to this inquiry.',
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Inquiries'

    def __str__(self):
        return f'{self.name} <{self.email}>'


class Article(models.Model):
    """An article the owner writes for the public 'Information' section."""

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PUBLISHED = 'published', 'Published'

    title = models.CharField(
        max_length=200,
        help_text="The article's headline, as it will appear on the website.",
    )
    slug = models.SlugField(
        max_length=220,
        unique=True,
        blank=True,
        help_text="Filled in automatically from the title.",
    )
    intro = models.CharField(
        max_length=300,
        blank=True,
        help_text="A short summary shown in the article list (optional — if left "
                  "blank, the start of the article is used).",
    )
    header_image = models.ImageField(
        upload_to='articles/%Y/%m/',
        blank=True,
        help_text="Optional photo shown at the top of the article and in the list.",
    )
    card_image = ImageSpecField(
        source='header_image',
        processors=[ResizeToFit(600, 400, upscale=False)],
        format='JPEG',
        options={'quality': 80},
    )
    banner_image = ImageSpecField(
        source='header_image',
        processors=[ResizeToFit(1600, 900, upscale=False)],
        format='JPEG',
        options={'quality': 85},
    )
    body = HTMLField(blank=True, help_text="Write your article here.")
    status = models.CharField(
        max_length=20,
        choices=Status,
        default=Status.DRAFT,
        help_text="“Draft” is only visible to you. “Published” shows on the website.",
    )
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="date published",
        help_text="Filled in automatically the first time the article is published.",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="date created")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="last updated")

    class Meta:
        ordering = ['-published_at', '-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['slug']),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('shop:article', args=[self.slug])

    @property
    def is_published(self):
        return self.status == self.Status.PUBLISHED

    @property
    def summary(self):
        if self.intro:
            return self.intro
        return Truncator(strip_tags(self.body)).words(40, truncate='…')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        # Stamp the publish date the first time it goes live.
        if self.status == self.Status.PUBLISHED and self.published_at is None:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)
