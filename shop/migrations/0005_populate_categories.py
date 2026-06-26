from django.db import migrations


def populate_categories(apps, schema_editor):
    Item = apps.get_model('shop', 'Item')
    for item in Item.objects.select_related('category').filter(category__isnull=False):
        item.categories.add(item.category)


def depopulate_categories(apps, schema_editor):
    Item = apps.get_model('shop', 'Item')
    for item in Item.objects.prefetch_related('categories'):
        first = item.categories.first()
        if first:
            item.category = first
            item.save(update_fields=['category'])


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0004_add_categories_m2m'),
    ]

    operations = [
        migrations.RunPython(populate_categories, reverse_code=depopulate_categories),
    ]
