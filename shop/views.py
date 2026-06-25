from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Case, IntegerField, When
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from .forms import InquiryForm
from .models import Article, Category, Item


def home(request):
    available = Item.objects.filter(
        status=Item.Status.AVAILABLE
    ).select_related('category').prefetch_related('images')
    return render(request, 'shop/home.html', {
        'featured_items': list(available.filter(featured=True)[:6]),
        'recent_items': available.order_by('-created_at')[:8],
        'categories': Category.objects.all(),
    })


def item_list(request, slug=None):
    category = None
    items = Item.objects.select_related('category').prefetch_related('images')
    if slug:
        category = get_object_or_404(Category, slug=slug)
        items = items.filter(category=category)

    # By default sold items are hidden; the "View sold items" toggle reveals them.
    show_sold = request.GET.get('sold') == '1'
    if not show_sold:
        items = items.exclude(status=Item.Status.SOLD)

    # Available/reserved first, sold last; newest first within each group.
    items = items.annotate(
        _sold_order=Case(
            When(status=Item.Status.SOLD, then=1),
            default=0,
            output_field=IntegerField(),
        )
    ).order_by('_sold_order', '-created_at')

    page_obj = Paginator(items, 24).get_page(request.GET.get('page'))
    return render(request, 'shop/item_list.html', {
        'category': category,
        'categories': Category.objects.all(),
        'page_obj': page_obj,
        'show_sold': show_sold,
    })


def item_detail(request, slug):
    item = get_object_or_404(
        Item.objects.select_related('category').prefetch_related('images'),
        slug=slug,
    )

    if request.method == 'POST':
        form = InquiryForm(request.POST)
        if form.is_valid():
            inquiry = form.save(commit=False)
            inquiry.item = item
            inquiry.save()
            messages.success(
                request,
                "Thank you — your message has been sent. We'll be in touch soon.",
            )
            # Post/Redirect/Get so a refresh doesn't resubmit the inquiry.
            return redirect(item.get_absolute_url())
    else:
        form = InquiryForm()

    related_items = (
        Item.objects.filter(category=item.category)
        .exclude(pk=item.pk)
        .exclude(status=Item.Status.SOLD)
        .select_related('category')
        .prefetch_related('images')
        .order_by('-created_at')
    )

    return render(request, 'shop/item_detail.html', {
        'item': item,
        'form': form,
        'related_items': related_items,
    })


def article_list(request):
    articles = Article.objects.filter(status=Article.Status.PUBLISHED)
    page_obj = Paginator(articles, 10).get_page(request.GET.get('page'))
    return render(request, 'shop/article_list.html', {'page_obj': page_obj})


def article_detail(request, slug):
    article = get_object_or_404(Article, slug=slug)
    # Drafts are visible only to staff (so the owner can preview before publishing).
    if not article.is_published and not request.user.is_staff:
        raise Http404('Article not found')
    return render(request, 'shop/article_detail.html', {'article': article})


def contact(request):
    return render(request, 'shop/contact.html')
