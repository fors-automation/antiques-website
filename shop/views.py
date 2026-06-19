from django.shortcuts import render


def home(request):
    return render(request, 'shop/home.html')


def contact(request):
    return render(request, 'shop/contact.html')
