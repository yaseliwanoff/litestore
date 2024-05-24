import json
import stripe
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseNotFound, JsonResponse
from django.urls import reverse_lazy, reverse
from .models import Product, OrderDetailModel
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView, DeleteView, TemplateView
from django.core.paginator import Paginator
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt


def index(request):
    page_obj = items = Product.objects.all()

    item_name = request.GET.get("search")
    if item_name != "" and item_name is not None:
        page_obj = items.filter(name__icontains=item_name)

    paginator = Paginator(page_obj, 3)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, "myapp/index.html", context)


class ProductListView(ListView):
    model = Product
    template_name = "myapp/index.html"
    context_object_name = "items"
    paginate_by = 3


# def indexItem(request, my_id):
#     item = Product.objects.get(id=my_id)
#     context = {"item": item}
#     return render(request, "myapp/detail.html", context=context)



# def index_item(request, my_id):
#     item = Product.objects.get(id=my_id)
#     context = {
#         'title': item.name,
#         'item': item,
#     }
#     return render(request, 'myapp/detail.html', context=context)


class ProductDetailView(DetailView):
    model = Product
    template_name = "myapp/detail.html"
    context_object_name = "item"
    pk_url_kwarg = "pk"

    def get_context_data(self, **kwargs):
        context = super(ProductDetailView, self).get_context_data(**kwargs)
        context["stripe_publishable_key"] = settings.STRIPE_PUBLISHABLE_KEY
        return context


@login_required
def add_item(request):
    """
    Add a new item to the database.

    This function handles the HTTP POST request to add a new item to the database.
    It expects the request to contain the following form fields:
    - name: The name of the item.
    - price: The price of the item.
    - description: The description of the item.
    - upload: The image file of the item.

    If the request method is POST, the function extracts the form data and creates a new
    Product object with the extracted data. The seller of the item is set to the current
    user making the request. The new item is then saved to the database.

    If the request method is not POST, the function does nothing and returns a render
    response to the "myapp/additem.html" template with a title of 'Добавить продукт на сайт'.

    Parameters:
    - request (HttpRequest): The HTTP request object.

    Returns:
    - HttpResponse: The rendered response to the "myapp/additem.html" template.
    """
    if request.method == "POST":
        name = request.POST.get("name")
        price = request.POST.get("price")
        description = request.POST.get("description")
        image = request.FILES["upload"]
        seller = request.user
        item = Product(name=name, price=price, description=description, image=image, seller=seller)
        item.save()

    return render(request, "myapp/additem.html", {'title': 'Add new product'})


@login_required
def update_item(request, my_id):
    """
    Updates an item in the database with the given ID.

    Parameters:
    - request (HttpRequest): The HTTP request object.
    - my_id (int): The ID of the item to be updated.

    Returns:
    - HttpResponse: The rendered response to the "myapp/updateitem.html" template.
    """
    item = Product.objects.get(id=my_id)
    if request.method == "POST":
        item.name = request.POST.get("name")
        item.price = request.POST.get("price")
        item.description = request.POST.get("description")
        item.image = request.FILES.get("upload", item.image)  # второй пункт что будет если элемент пустой
        item.save()

        return redirect('myapp:homepage')

    context = {
        'title': f'Update item {item.name}',
        'item': item,
    }

    return render(request, 'myapp/updateitem.html', context)


# @login_required
# def delete_item(request, my_id):
#     """
#     Deletes an item from the database with the given ID.

#     Parameters:
#     - request (HttpRequest): The HTTP request object.
#     - my_id (int): The ID of the item to be deleted.

#     Returns:
#     - HttpResponseRedirect: A redirect response to the "myapp:homepage" URL.
#     """
#     item = Product.objects.get(id=my_id)
#     if request.method == "POST":
#         item.delete()

#         return redirect('myapp:homepage')

#     context = {
#         'title': f'Delete item {item.name}',
#         'item': item,
#     }

#     return render(request, 'myapp/deleteitem.html', context)


@login_required
class ProductDeleteView(DeleteView):
    model = Product
    success_url = reverse_lazy('myapp:homepage')


@csrf_exempt
def create_checkout_session(request, id):
    product = get_object_or_404(Product, pk=id)

    stripe.api_key = settings.STRIPE_SECRET_KEY
    checkout_session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": product.name,
                    },
                    "unit_amount": int(product.price * 100),
                },
                "quantity": 1,
            }
        ],
        mode="payment",
        success_url=request.build_absolute_uri(reverse("myapp:success"))
        + "?session_id={CHECKOUT_SESSION_ID}",
        cancel_url=request.build_absolute_uri(reverse("myapp:failed")),
    )

    # OrderDetail.objects.create(
    #     customer_email=email,
    #     product=product, ......
    # )

    order = OrderDetailModel()
    order.product = product
    order.stripe_payment_intent = checkout_session["payment_intent"]
    order.amount = int(product.price * 100)
    order.save()

    # return JsonResponse({'data': checkout_session})
    return JsonResponse({"sessionId": checkout_session.id})

class PaymentSuccessView(TemplateView):
    template_name = "myapp/payment_success.html"

    def get(self, request, *args, **kwargs):
        session_id = request.GET.get("session_id")
        if session_id is None:
            return HttpResponseNotFound()

        stripe.api_key = settings.STRIPE_SECRET_KEY
        session = stripe.checkout.Session.retrieve(session_id)

        order = get_object_or_404(
            OrderDetailModel, stripe_payment_intent=session.payment_intent
        )
        order.has_paid = True
        order.save()
        return render(request, self.template_name)


class PaymentFailedView(TemplateView):
    template_name = "myapp/payment_failed.html"