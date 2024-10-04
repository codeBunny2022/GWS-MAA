from django.urls import path
from .views import oauth2_login, oauth2_callback, GetResponseView

urlpatterns = [
    path('oauth2login/', oauth2_login, name='oauth2login'),
    path('oauth2callback/', oauth2_callback, name='oauth2callback'),
    path('', GetResponseView.as_view(), name='get_response'),
]