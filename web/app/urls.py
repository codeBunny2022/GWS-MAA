# app/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.GetResponseView.as_view(), name='get_response'),
]