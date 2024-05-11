from django.urls import path
from . import views

app_name = 'myapp'

urlpatterns = [
    path('', views.index, name='homepage'),
    path('<int:my_id>/', views.index_item, name='detail'),
]

