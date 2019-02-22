from django.urls import path
from . import views


urlpatterns = [
    path('oauth_get_token', views.oauth_get_token, name='oauth_get_token'),
    path(r'authorize_account/<int:account_id>', views.authorize_account, name='authorize_account'),
]

