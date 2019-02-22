"""
Gateway clients are abstractions that is aimed to serve as http-request-response processors.
That is not for a business logic, but for any http processing logic like: sending http request, handling connection
errors and
timeouts etc. Response data should be processed in a gateway or gateway's client code
"""
import json
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor, Future
from logging import getLogger
from uuid import uuid4

import requests
from requests.adapters import HTTPAdapter, Retry

from .exceptions import ConfigError, PayloadError
from .oauth import YandexDirectAuth, Authorizable, YandexOAuth

_logger = getLogger(__name__)


__all__ = ['YandexOauthClient', 'AsyncGatewayHttpClient', 'YandexDirectClient', 'Authorizable']


class HttpResponseResult:

    def __init__(self, response: requests.Response):
        self.response = response
        self.data = None

    def result(self):
        try:
            # Try getting json from response
            self.data = self.response.json()
        except json.JSONDecodeError:
            # Get bytes context
            self.data = self.response.content or self.response.reason
            try:
                # Try loading bytes to json
                self.data = json.loads(self.data)
            except json.JSONDecodeError:
                # Try at least decode bytes into string
                self.data = self.data if not type(self.data) is bytes else self.data.decode()
        return self


class AsyncHttpResponseResult:

    def __init__(self, result: Future):
        self._result = result

    def result(self):
        return self._result.result().result()


class GatewayHttpClient:
    """
    Base client to send http-requests

    This class is entended to be subclassed. You may configure request preaparation logic
    by overriding _make_payload and prepare_request methods in subclasses:

        client = GatewayHttpClient()
        # request params are the same as requests.Request
        p_request = client.prepare_request(method='POST', url='http://...',**kwargs['json', 'data', 'params', ...]
        response = client.send(p_request)

    """

    DEFAULT_CONFIG = {
        'retry': Retry(status=3, total=10, connect=3, backoff_factor=0.5,
                       status_forcelist=[502, 500, 524, 423, 400],
                       method_whitelist=False, raise_on_status=False),
        'default_request_timeout': 15,
        'http_methods_allowed': ('GET', 'HEAD', 'POST', 'DELETE', 'PUT'),
        'connection_pool_size': requests.adapters.DEFAULT_POOLSIZE
    }

    def __init__(self, **kwargs):
        self.__session = self._retry_policy = None
        self._config = self.DEFAULT_CONFIG.copy()
        self.headers = {}
        self.configure(**kwargs)

    @property
    def configured(self) -> bool:
        return self._retry_policy is not None

    def configure(self, **kwargs):
        self._config.update(kwargs)
        self.set_retry_policy(self._config['retry'])

    def set_retry_policy(self, retry):
        if not any([
            issubclass(type(retry), Retry),
            type(retry) is int
        ]):
            raise ConfigError(f'Bad retry policy set. Expected {type(Retry)} or {int}, got {type(retry)}')
        self._retry_policy = retry

    def send(self, **kwargs) -> HttpResponseResult:
        if not self.configured:
            raise ConfigError(f'{self.__class__.__name__} was not properly configured.')
        p_request = self._prepare_request(**kwargs)
        response = self._send(p_request)
        return HttpResponseResult(response)

    def _make_payload(self, **kwargs) -> tuple:
        """Controlls request payload preparation. Http-request should have at least method and url params"""
        required = ('method', 'url')
        try:
            assert all(i in kwargs for i in required), f'Wrong payload! You must provide at least "method" and "url"' \
                f' parameters for {self.__class__.__name__} payload'
            method, url = [kwargs.pop(j) for j in required]
            assert method in self._config['http_methods_allowed'], 'Http method is not allowed or unsupported'
            if method == 'GET' and any(['data' in kwargs, 'json' in kwargs]):
                raise AssertionError('Use params with GET method')
            if method == 'POST' and 'params' in kwargs:
                raise AssertionError('Use data or json with POST method')
        except (AssertionError, KeyError) as e:
            raise PayloadError(e)
        return method, url, kwargs

    def _prepare_request(self, **kwargs) -> requests.PreparedRequest:
        """
        Constructs prepared request object. This is where we can perform request configuration like headers update
        authentication etc.
        """
        payload = self._make_payload(**kwargs)
        method, url, other = payload
        try:
            p_request = requests.Request(method, url, **other).prepare()
            self.headers.update(p_request.headers)
            p_request.prepare_headers(self.headers)
        except Exception as e:
            raise PayloadError(e)
        else:
            return p_request

    @property
    def _session(self) -> requests.Session:
        """
        Singleton http-session object. Only one session used for every client's object
        :rtype: `requests.Session <http://docs.python-requests.org/en/master/user/advanced/#session-objects>`_
        """
        if not self.__session:
            self.__session = requests.Session()
            # Default requests.Session() object does not retry requests if they fail
            # Here we can apply retry policy to handle failed requests
            # more info [http://docs.python-requests.org/en/master/api/#requests.adapters.HTTPAdapter]
            retry_adapter = HTTPAdapter(max_retries=self._retry_policy,
                                        pool_maxsize=self._config['connection_pool_size'],
                                        pool_connections=self._config['connection_pool_size'])
            self.__session.mount('https://', retry_adapter)
            self.__session.mount('http://', retry_adapter)
        return self.__session

    def _send(self, prepared_request: requests.PreparedRequest) -> requests.Response:
        """
        This is the main method that sends requests and handles responses and connection errors.
        No logic except sending request and handling data transfer errors should be implemented here.

        :param prepared_request: requests library object that is passed to session.send() method
        :type prepared_request: `requests.PreparedRequest \
        <http://docs.python-requests.org/en/master/api/#requests.PreparedRequest>`_
        :rtype: `requests.Response <http://docs.python-requests.org/en/master/api/#requests.Response>`_
        """
        _logger.debug(
            f'[REQUEST]\n'
            f'[URL]: {prepared_request.url}\n'
            f'[METHOD]: {prepared_request.method}\n'
            f'[BODY]: {prepared_request.body}\n'
            f'[HEADERS]: {prepared_request.headers}\n'
            f'[/REQUEST]\n'
        )
        response = self._session.send(prepared_request, timeout=self._config['default_request_timeout'])
        _logger.debug(f'[RESPONSE]\n'
                      f'[STATUS]: {response.status_code}\n'
                      f'[HEADERS]: {response.headers}\n'
                      f'[CONTENT]: {response.content}\n'
                      f'[/RESPONSE]\n')

        return response


class AsyncGatewayHttpClient(GatewayHttpClient):
    """
    Http client to perform async-http requests:

        client = ReadWriteHttpClient()
        client.set_auth_data(token='123')
        pool_id = client.get_pool_id()
        for i in range(5)
            client.pool_send(pool_id, method='POST', url='http://hello.world', json={'a':i}
        for response, payload in client.pool_receive(pool_id):
            yield response.result().data

    """
    def __init__(self, max_workers=4, **kwargs):
        super().__init__(connection_pool_size=max_workers, **kwargs)
        self.__executor = ThreadPoolExecutor(max_workers=max_workers)
        self.__results_buffer = defaultdict(deque)

    def get_pool_id(self) -> str:
        return str(uuid4())

    def pool_send(self, pool_id: str, **kwargs):
        """
        Executes http_requests in async manner with threaded executor.
        Future results are saved to queue with buffer_id key

        :param pool_id:     Unique buffer id from where async-results will be readed later
        :type pool_id:      str
        :param kwargs:      http-request params (same as requests.Request params)
        :return:
        """
        future = self.__executor.submit(self.send, **kwargs)
        self.__results_buffer[pool_id].append((future, kwargs))

    def pool_receive(self, pool_id: str) -> [(AsyncHttpResponseResult, dict)]:
        """
        Get async results from queue with buffer_id and yields them as they are ready
        :param pool_id:     queue id to read from
        :return:            iterable of 2-tuples: with async result and request payload
        :rtype:             Iterable[(HttpResponseResult, dict)]
        """
        while self.__results_buffer[pool_id]:
            future, payload = self.__results_buffer[pool_id].popleft()
            if future.done():
                yield AsyncHttpResponseResult(future), payload
            else:
                self.__results_buffer[pool_id].append((future, payload))
        del self.__results_buffer[pool_id]


class YandexOauthClient(GatewayHttpClient, Authorizable):

    def set_auth_data(self, **kwargs):
        try:
            self.auth_data = YandexOAuth(
                client_id=kwargs.get('client_id'),
                client_secret=kwargs.get('client_secret')
            )
        except AssertionError as e:
            raise ConfigError(e)
        else:
            self.authorized = True

    def _make_payload(self, **kwargs):
        method, url, other = super()._make_payload(**kwargs)
        data: dict = other.get('data', None)
        if not (data or type(data) is dict):
            raise PayloadError('"data" dictionary parameter required')
        data.update(self.auth_data())
        return method, url, other


class YandexDirectClient(AsyncGatewayHttpClient, Authorizable):

    @property
    def configured(self):
        return self.authorized and super().configured

    def set_auth_data(self, **kwargs):
        try:
            self.auth_data = YandexDirectAuth(token=kwargs.get('token'))
        except AssertionError as e:
            raise ConfigError(e)
        else:
            self.authorized = True

    def _prepare_request(self, **kwargs):
        p_request = super()._prepare_request(**kwargs)
        p_request.prepare_auth(auth=self.auth_data)
        return p_request
