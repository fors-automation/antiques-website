from django.contrib import admin

from .models import Category, Inquiry, Item, ItemImage


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


class ItemImageInline(admin.TabularInline):
    model = ItemImage
    extra = 1
    fields = ('image', 'alt_text', 'sort_order')


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'category', 'price', 'currency',
        'status', 'featured', 'created_at',
    )
    list_filter = ('status', 'category', 'featured', 'condition')
    list_editable = ('status', 'featured')
    search_fields = ('title', 'description', 'provenance')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at', 'sold_at')
    date_hierarchy = 'created_at'
    inlines = [ItemImageInline]


@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'item', 'handled', 'created_at')
    list_filter = ('handled', 'created_at')
    list_editable = ('handled',)
    search_fields = ('name', 'email', 'message')
    readonly_fields = ('created_at',)
