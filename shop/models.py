from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from imagekit.models import ImageSpecField
from pilkit.processors import ResizeToFit


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


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

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='items',
    )
    # Money is stored as Decimal, never float. Currency is recorded explicitly.
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(
        max_length=20,
        choices=Status,
        default=Status.AVAILABLE,
    )
    condition = models.CharField(
        max_length=20,
        choices=Condition,
        blank=True,
    )
    era = models.CharField(
        max_length=100,
        blank=True,
        help_text='Period or era, e.g. "Victorian", "Art Deco", "1960s".',
    )
    dimensions = models.CharField(
        max_length=255,
        blank=True,
        help_text='Free text, e.g. "H 90 × W 45 × D 30 cm".',
    )
    provenance = models.TextField(
        blank=True,
        help_text='History or origin notes for this piece.',
    )
    featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    sold_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['slug']),
        ]

    def __str__(self):
        return self.title

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
    image = models.ImageField(upload_to='items/%Y/%m/')

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
        help_text='Short description of the photo for accessibility and SEO.',
    )
    sort_order = models.PositiveIntegerField(default=0)

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
