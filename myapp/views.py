from django.shortcuts import render
from django.http import HttpResponse
from .models import Product


def index(request):
    items = Product.objects.all()
    return render(request, 'myapp/index.html', {
        'title': 'Главная страница',
        'items': items,
    })


def index_item(request, my_id):
    item = Product.objects.get(id=my_id)
    context = {
        'title': item.name,
        'item': item,
    }
    return render(request, 'myapp/detail.html', context=context)
