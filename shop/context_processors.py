from .models import Category


def navigation(request):
    """Expose categories site-wide (used by the footer site map)."""
    return {'nav_categories': Category.objects.all()}
