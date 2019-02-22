from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.http import HttpRequest
from django.shortcuts import redirect, reverse
from django.views.decorators.cache import never_cache

from .controllers import get_client_login, get_oauth_token
from . import controllers
from common.http import oauth, exceptions

@never_cache
def authorize_account(request: HttpRequest, account_id: int):
    """Redirect to Yandex OAuth API"""
    api_url = f'{oauth.YANDEX_OAUTH_URL}/authorize'
    host = settings.CALLBACK_HOST if settings.DEBUG else request.get_host()
    params = {
        'response_type': 'code',
        'client_id': settings.YD_CLIENT_ID,
        'redirect_uri': f'{request.scheme}://{host}{reverse("oauth_get_token")}',
        'state': account_id,
        'force_confirm': 1      # tell yandex api to ask permission even if user has already logged in
    }
    return redirect(f'{api_url}?{urlencode(params)}')


@never_cache
def oauth_get_token(request: HttpRequest):
    """
    Callback function that is called by Yandex Direct OAuth API.
    This will get 'code' parameter from response and will make subsequent request
    to retrieve access token.
    """
    error = request.GET.get(key='error')
    if error:
        messages.error(request, request.GET.get(key='error_description'))
    else:
        access_code = request.GET.get(key='code')
        account_id = request.GET.get(key='state')
        # get auth token with access code
        token = get_oauth_token({'grant_type': 'authorization_code', 'code': access_code})
        if not int(account_id):
            try:
                client_login = get_client_login(token)
            except exceptions.UnExpectedResult as e:
                messages.error(request, e)
            else:
                account = controllers.create_account_with_login(client_login)
                controllers.set_account_token(account.id, token)
    return redirect('/account')
