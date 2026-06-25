from django.contrib import admin, messages
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import Article, Category, Inquiry, Item, ItemImage

# Friendly branding for the owner's management interface.
admin.site.site_header = 'Glory Days Past'
admin.site.site_title = 'Glory Days Past'
admin.site.index_title = 'Manage your shop'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'item_count')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)
    # The web address part is filled in for you from the name.
    fields = ('name', 'slug')

    @admin.display(description='Items in this category')
    def item_count(self, obj):
        return obj.items.count()


class ItemImageInline(admin.TabularInline):
    model = ItemImage
    extra = 1
    fields = ('preview', 'image', 'alt_text', 'sort_order')
    readonly_fields = ('preview',)
    verbose_name = 'photo'
    verbose_name_plural = 'Photos (you can add several — drag the display order)'

    @admin.display(description='Current photo')
    def preview(self, obj):
        if obj and obj.pk and obj.image:
            return format_html(
                '<img src="{}" style="height:70px;width:auto;border-radius:4px;" />',
                obj.thumbnail.url,
            )
        return '—'


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    # --- List view: photo, title, category, price, status (+ quick toggles) ---
    list_display = (
        'thumb', 'title', 'category', 'price_display', 'status', 'featured',
    )
    list_display_links = ('thumb', 'title')
    list_editable = ('status', 'featured')
    list_filter = ('status', 'category', 'featured', 'condition')
    search_fields = ('title', 'description', 'era', 'provenance')
    search_help_text = 'Search by title, description, era, or provenance.'
    date_hierarchy = 'created_at'
    list_per_page = 25
    save_on_top = True
    empty_value_display = '—'
    actions = ('mark_as_sold', 'mark_as_available')

    # --- Change form: grouped into friendly sections ---
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at', 'sold_at')
    inlines = [ItemImageInline]
    fieldsets = (
        ('The basics', {
            'fields': ('title', 'category', 'price', 'currency', 'status', 'featured'),
        }),
        ('Details buyers care about', {
            'fields': ('description', 'condition', 'era', 'dimensions', 'provenance'),
        }),
        ('Housekeeping', {
            'classes': ('collapse',),
            'description': "You can usually ignore this section — it's filled in "
                           "automatically.",
            'fields': ('slug', 'created_at', 'sold_at'),
        }),
    )

    def get_queryset(self, request):
        # Prefetch photos so the thumbnail column doesn't run a query per row.
        return super().get_queryset(request).prefetch_related('images')

    @admin.display(description='Photo')
    def thumb(self, obj):
        images = list(obj.images.all())
        if images:
            return format_html(
                '<img src="{}" alt="" style="height:48px;width:auto;'
                'border-radius:4px;object-fit:cover;" />',
                images[0].thumbnail.url,
            )
        return mark_safe('<span style="color:#999;">No photo</span>')

    @admin.display(description='Price', ordering='price')
    def price_display(self, obj):
        return f'{obj.price:,.2f} {obj.currency}'

    @admin.action(description='Mark selected items as Sold')
    def mark_as_sold(self, request, queryset):
        updated = 0
        for item in queryset.exclude(status=Item.Status.SOLD):
            item.status = Item.Status.SOLD
            item.save()
            updated += 1
        self.message_user(
            request,
            f'{updated} item(s) marked as sold.',
            level=messages.SUCCESS,
        )

    @admin.action(description='Mark selected items as Available')
    def mark_as_available(self, request, queryset):
        skipped = queryset.filter(status=Item.Status.SOLD).count()
        updated = 0
        for item in queryset.exclude(status=Item.Status.SOLD):
            item.status = Item.Status.AVAILABLE
            item.save()
            updated += 1
        message = f'{updated} item(s) marked as available.'
        if skipped:
            message += (f' {skipped} already-sold item(s) were left unchanged — '
                        '“sold” is permanent.')
        self.message_user(
            request,
            message,
            level=messages.WARNING if skipped else messages.SUCCESS,
        )


@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'item', 'handled', 'created_at')
    list_filter = ('handled', 'created_at')
    list_editable = ('handled',)
    search_fields = ('name', 'email', 'message')
    date_hierarchy = 'created_at'
    # Inquiries come from customers — show them as read-only so the message
    # can't be altered by mistake; only "handled" stays editable.
    readonly_fields = ('name', 'email', 'message', 'item', 'created_at')
    fields = ('name', 'email', 'item', 'message', 'created_at', 'handled')

    def has_add_permission(self, request):
        # Inquiries are created by customers via the site, not added by hand.
        return False


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'published_at', 'updated_at')
    list_filter = ('status',)
    list_editable = ('status',)
    search_fields = ('title', 'intro', 'body')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'published_at'
    readonly_fields = ('created_at', 'updated_at', 'published_at')
    save_on_top = True
    fieldsets = (
        ('Write your article', {
            'fields': ('title', 'intro', 'header_image', 'body', 'status'),
        }),
        ('Housekeeping', {
            'classes': ('collapse',),
            'description': "Filled in automatically — you can usually ignore this.",
            'fields': ('slug', 'published_at', 'created_at', 'updated_at'),
        }),
    )
