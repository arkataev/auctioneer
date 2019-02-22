"""
Yandex Oauth API interaction controllers
"""

from requests import Request
from requests.auth import AuthBase

YANDEX_OAUTH_URL = 'https://oauth.yandex.ru'


class Authorizable:
    """Interface providing abilty to set authorization data on clients"""

    auth_data: AuthBase
    authorized: bool = False

    def set_auth_data(self, **kwargs): ...


class YandexDirectAuth(AuthBase):

    def __init__(self, token):
        assert token, 'Token required'
        self._token = token

    def __call__(self, request: Request):
        request.headers['Authorization'] = f'Bearer {self._token}'
        return request


class YandexOAuth(AuthBase):

    def __init__(self, client_id, client_secret):
        assert client_id, 'Client id required'
        assert client_secret, 'Client secret required'
        self._client_id = client_id
        self._client_secret = client_secret

    def __call__(self, *args, **kwargs):
        return {'client_id': self._client_id, 'client_secret': self._client_secret}
