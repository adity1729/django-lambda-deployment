from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health_check, name='health-check'),
    path('calculate/', views.calculate, name='calculate'),
    path('hello/', views.hello_async),
    path('process/', views.process_data),
]