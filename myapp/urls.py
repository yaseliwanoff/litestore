from django.urls import path
from . import views
from myapp.views import ProductListView, ProductDetailView, DeleteView, PaymentSuccessView, PaymentFailedView

app_name = 'myapp'

urlpatterns = [
    path('', views.index, name='homepage'),
    # path('', ProductListView.as_view(), name='homepage'),
    path('<int:pk>/', ProductDetailView.as_view(), name='detail'),
    path('additem/', views.add_item, name='add_item'),
    path('update/<int:my_id>/', views.update_item, name='update_item'),
    path('delete/<int:my_id>/', DeleteView.as_view(), name='delete_item'),
    path('success/<int:my_id>/', PaymentSuccessView.as_view(), name='success'),
    path('failed/<int:my_id>/', PaymentFailedView.as_view(), name='failed'),
    path('api/checkout-session/<int:id>/', DeleteView.as_view(), name='api_checkout_session'),
]
