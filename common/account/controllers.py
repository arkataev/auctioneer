"""
Account model operations implementations
"""

from django.conf import settings

from .models import Account
from ..http import oauth
from ..http.gateway import YandexDirectGateway, OAuthGateway
from . import costants as const

def set_account_token(account_id: int, token: str, force: bool = False) -> int:
    """
    Check if account already has token or we try to set new token from yandex api.
    If no token exists and no token got from yandex api, than we should disable account

    :param account_id:      unique database account id
    :type account_id:       int
    :param token:           yandex auth api token
    :type token:            str
    :param force:           reset token forcely even if one exists
    :type force:            bool
    :rtype:                 int
    :returns:                0 if token was set successfully
    :returns:                1 if token was NOT set successfully
    """
    result = 1
    try:
        account = Account.objects.get(id=account_id)
    except Account.DoesNotExist:
        pass
    else:
        account.token = account.token or token if not force else token
        if account.token:
            account.enabled = True
        account.save()
        result = 0
    return result


def create_account_with_login(login: str) -> Account:
    """
    Create new or get existing account with login provided

    :param login:           login to create new Account with
    :type login:            str
    :rtype: Account
    """
    account, created = Account.objects.get_or_create(login=login, acc_type=1)
    return account


def get_oauth_token(auth_params: dict) -> str:
    """
    Get oauth token from Yandex auth API. More info on Oauth process
    `here <https://tech.yandex.com/oauth/doc/dg/reference/auto-code-client-docpage/>`_::

        token = get_oauth_token({'grant_type': 'authorization_code', 'code': 'oauth_access_code'}})

    :param auth_params:         mainly this should be only 'grant_type' and 'code' params \
    other auth params will be inserted on func execution
    :type auth_params:          dict
    :rtype:                     str
    :return:                    yandex oauth token string
    """
    api_url = f'{oauth.YANDEX_OAUTH_URL}/token'
    gw = OAuthGateway(client_id=settings.YD_CLIENT_ID, client_secret=settings.YD_CLIENT_SECRET)
    token = gw.get_oauth_token(api_url, **auth_params)
    return token


def get_client_login(token: str) -> str:
    """
    Get client login from Yandex API.
    This is mainly a helper function to get current authorized client login from yandex api.
    It can be used to autofill some userdata.

    :param token:       yandex ouath token
    :type token:        str
    :return:            authenticated user login from yandex
    :rtype:             str
    """
    gateway = YandexDirectGateway(token=token)
    result = gateway.get_client_login()
    return result


def make_yd_gateway(account_id: int) -> YandexDirectGateway:
    """
    Create and return authorized YandexDirectGateway for a given account.

    :param account_id:          account id which gateway should use to authorize
    :type account_id:           int
    :rtype: YandexDirectGateway
    """
    account = Account.objects.get(id=account_id)
    assert account.acc_type == const.YD_ACCOUNT_TYPE, f'Wrong account type. ' \
        f'Expected {const.YD_ACCOUNT_TYPE}, got {account.acc_type}'
    gateway = YandexDirectGateway(token=account.token)
    return gateway

