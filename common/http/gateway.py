"""
Represents a particular data source that client wants to use to exchange data, for example for network resources
and databases and provides interfaces that can be used by client.
Data exchange logic is abstracted to separate layer as this is not a part of main business model and tend to
change.
"""
from logging import getLogger
from types import GeneratorType

from common import signals
from . import constants
from .client import YandexOauthClient, YandexDirectClient, Authorizable
from .exceptions import UnExpectedResult
from .retry import gateway_retry
from .utils import formatter, Chunker

__all__ = ['YandexDirectGateway', 'OAuthGateway']
_logger = getLogger(__name__)


class AuthorizableGateway:
    """
    Gateway base class.
    Gateway class should provide an API of source that is represented by the gateway.
    Client's code will use API to exchange data with the source.
    """
    client: Authorizable

    def __init__(self, **auth_data):
        self.client.set_auth_data(**auth_data)
        assert self.client.authorized, 'Gateway client was not authorized'


class YandexDirectGateway(AuthorizableGateway):
    """
    Gateway for exchanging data with Yandex Direct API.

    Essentially, this class implements API methods of Yandex Direct API and contains some basic logic concerning
    data retrieving and processing. There should be no bussiness logic here as Gateway class is an abstraction
    of data source not a core app logic.
    """

    client = YandexDirectClient()

    default_api_url = "https://api.direct.yandex.com"  #: yandex direct api base url
    api_version = 'v5'  #: yandex direct api version that is used by gateway
    endpoints = constants.YdAPiV5EndpointsStruct  #: yandex direct api endpoints

    def get_api_url(self) -> str:
        return f'{self.default_api_url}/json/{self.api_version}'

    @staticmethod
    def get_response_result(response):
        try:
            result = response.get('result') or response.get('error')
        except AttributeError:
            result = response
        return result or {}

    def paginated_result(self, result, pool_id=None, **kwargs) -> GeneratorType:
        # Yandex Direct API response query is limited by 10 000 items by default, if more items present in query
        # we should repeat request with LimitedBy as offset parameter.
        # more info here https://tech.yandex.ru/direct/doc/dg/best-practice/get-docpage/
        if 'LimitedBy' in result:
            yield result
            kwargs['json']['params'].update({'Page': {'Offset': result['LimitedBy']}})
            if pool_id:
                self.client.pool_send(pool_id, **kwargs)
            else:
                result = self.get_response_result(self.client.send(**kwargs).result().data)
                yield from self.paginated_result(result, **kwargs)
        else:
            yield result

    @gateway_retry(retry_codes=[52, 1000, 1001, 1002])
    def keyword_bids_gen(self, selection_criteria: dict,
                         field_names: list = constants.YD_KEYWORD_BIDS_FIELDNAMES,
                         search_field_names: list = constants.YD_KEYWORD_BIDS_SEARCH_FIELDS,
                         network_field_names: list = constants.YD_KEYWORD_BIDS_NETWORK_FIELDS) -> GeneratorType:
        """
        This is a generator for keywords bids items in yandex direct api. Default request returns up to 10 000 keyword
        bid items, though we should repeat request until all keyword items recieved. This method will fetch one package
        of keyword bids at a time (package <= 10 000 items) until exhausted. For more info consider reading
        `API Docs <https://tech.yandex.ru/direct/doc/ref-v5/keywordbids/get-docpage/>`_::

            keyword_bids_params = {
                'selection_criteria' : {
                    'AdGroupIds': [1,2,3],          # Select all keyword bids that correspond to given AdGroup ids
                    'CampaignIds': [4,5,6],         # Select all kw_bids that correspond to given CampaignIds
                    'KeywordIds': [7,8,9]           # Select given keyword ids
                },
                'field_names': [],
                'search_field_names': [],
                'network_field_names': []
            }

        Basically you may provide only 'selection_criteria' parameter as others are already set to default values

        :param selection_criteria:          keyword bids selection criteria. You may provide one of three keys \
        that represent keyword bid groups. Values should be a list of ids that correspond to a given group
        :type selection_criteria:           dict
        :param field_names:                 fields that should be requested from YD API
        :type field_names:                  list
        :param search_field_names:          fields that should be included in Search entities
        :type search_field_names:           list
        :param network_field_names:         fields that should be included in Network entities
        :type network_field_names:          list
        :rtype: GeneratorType
        :returns:                           A generator of keyword bids json - data
        """

        api_url = f'{self.get_api_url()}/{self.endpoints.KEYWORD_BIDS}'
        pool_id = self.client.get_pool_id()
        limits = {'KeywordIds': 10_000, 'AdGroupIds': 1000, 'CampaignIds': 10}
        key = next(iter(selection_criteria))
        payload = {
            'method': 'get',
            'params': {
                'SelectionCriteria': selection_criteria,
                'FieldNames': field_names,
                'SearchFieldNames': search_field_names or [],
                'NetworkFieldNames': network_field_names or []
            }
        }
        for chunk in Chunker(items=selection_criteria[key], limit=limits[key]):
            payload['params']['SelectionCriteria'] = {key: chunk}
            self.client.pool_send(pool_id, method='POST', url=api_url, json=payload)
        for response, request_payload in self.client.pool_receive(pool_id):
            result = self.get_response_result(response.result().data)
            paginated = self.paginated_result(result, pool_id=pool_id, **request_payload)
            yield from formatter(paginated, key='KeywordBids')

    @signals.params_interceptor.intercept
    @gateway_retry(retry_codes=[52, 1000, 1001, 1002])
    def set_keyword_bids(self, data: [dict]) -> GeneratorType:
        """
        Set new bids on given keywords in Yandex Direct API.

        You must provide a collection of keyword bids data that complies to \
        `YD Keyword bid set API <https://tech.yandex.ru/direct/doc/ref-v5/keywordbids/set-docpage/>`_.::

            keyword_bids_data = [{'KeywordId': 123, 'SearchBid':1000} ... ]

        :param data:            a collection of keyword bids data
        :type data:             list
        :rtype:                 Iterator[dict]
        :return:                YD *keyword bids set* response structure
        """
        api_url = f'{self.get_api_url()}/{self.endpoints.KEYWORD_BIDS}'
        queue = self.client.get_pool_id()
        payload = {
            'method': 'set',
            'params': {
                'KeywordBids': data
            }
        }
        for chunk in Chunker(data, limit=10000):
            payload['params']['KeywordBids'] = chunk
            self.client.pool_send(queue, method='POST', url=api_url, json=payload)
        for response, _ in self.client.pool_receive(queue):
            result = self.get_response_result(response.result().data)
            yield from formatter(result, 'SetResults')

    def get_client_login(self) -> str:
        """
        Get login of currently authorized in Yandex Direct API user.

        :rtype:     list
        :return:    login of currently authorized in YD API user
        :raises:    UnExpectedResult if no login data received
        """
        api_url = f'{self.get_api_url()}/{self.endpoints.CLIENTS}'
        data = {
            "method": "get",
            "params": {
                "FieldNames": ["Login"]
            }
        }
        response = self.client.send(method='POST', url=api_url, json=data)
        result = self.get_response_result(response.result().data)
        try:
            clients = result.get('Clients')
        except AttributeError as e:
            raise UnExpectedResult(e)
        else:
            if not clients:
                raise UnExpectedResult(result.get('error_string', result))
            login = next(iter(clients)).get('Login')
            if not login:
                raise UnExpectedResult(clients)
            return login

    @gateway_retry(retry_codes=[52, 1000, 1001, 1002])
    def get_campaigns(self, selection_criteria: dict,
                      field_names=constants.YD_CAMPAIGNS_FIELDNAMES, **kwargs) -> GeneratorType:
        """
        Yandex Direct campaigns generator.
        This method will fetch one package
        of keyword bids at a time (package <= 10 000 items) until exhausted. For more info consider get_asyncing
        `API Docs <https://tech.yandex.ru/direct/doc/ref-v5/campaigns/get-docpage/>`_::

            # keys should be in snake_case, but values - in CamelCasee
            gateway.get_campaigns(selection_criteria={
                "Ids": [1,2,3],
                "Types":[1,2,3]
                "States": [1,2,3],
                ...},
                field_names = [...],
                text_campaign_field_names: [...],
                mobile_app_campaign_field_names: [...],
                ...
                )
        :param selection_criteria:
        :type selection_criteria:           dict
        :param field_names:
        :type field_names:                  list
        :param kwargs:     api parameters. For full list of params see
         `API Docs <https://tech.yandex.ru/direct/doc/ref-v5/campaigns/get-docpage/>`_.
         Use snake-cased key-value params. Page parameter is ignored.
        :rtype:             GeneratorType
        :return:            Generator of yandex direct campaigns for a given acccount
        """
        api_url = f'{self.get_api_url()}/{self.endpoints.CAMPAIGNS}'
        payload = {
            'method': 'get',
            'params': {
                'SelectionCriteria': selection_criteria,
                'FieldNames': field_names,
                'TextCampaignFieldNames': kwargs.get('text_campaign_field_names', []),
                'MobileAppCampaignFieldNames': kwargs.get('mobile_app_campaign_field_names', []),
                'DynamicTextCampaignFieldNames': kwargs.get('dynamic_text_campaign_field_names', []),
                'CpmBannerCampaignFieldNames': kwargs.get('cpm_banner_campaign_field_names', [])
            }
        }
        response = self.client.send(method='POST', url=api_url, json=payload)
        result = self.get_response_result(response.result().data)
        paginated = self.paginated_result(result, method='POST', url=api_url, json=payload)
        yield from formatter(paginated, key='Campaigns')

    @gateway_retry(retry_codes=[52, 1000, 1001, 1002])
    def get_ads(self, selection_criteria: dict,
                field_names=constants.YD_ADS_FIELDNAMES, **kwargs) -> GeneratorType:
        """"""
        api_url = f'{self.get_api_url()}/{self.endpoints.ADS}'
        payload = {
            'method': 'get',
            'params': {
                'SelectionCriteria': selection_criteria,
                'FieldNames': field_names,
                'TextAdFieldNames': kwargs.get('text_ad_field_names', []),
                'MobileAppAdFieldNames': kwargs.get('mobile_app_ad_field_names', []),
                'DynamicTextAdFieldNames': kwargs.get('dynamic_text_ad_field_names', []),
                'TextImageAdFieldNames': kwargs.get('text_image_ad_field_names', []),
                'MobileAppImageAdFieldNames': kwargs.get('mobile_app_image_ad_field_names', []),
                'TextAdBuilderAdFieldNames': kwargs.get('text_ad_builder_ad_field_names', []),
                'MobileAppAdBuilderAdFieldNames': kwargs.get('mobile_app_ad_builder_ad_field_names', []),
                'CpcVideoAdBuilderAdFieldNames': kwargs.get('cpc_video_ad_builder_ad_field_names', []),
                'CpmBannerAdBuilderAdFieldNames': kwargs.get('cpm_banner_ad_builder_ad_field_names', []),
            }
        }
        response = self.client.send(method='POST', url=api_url, json=payload)
        result = self.get_response_result(response.result().data)
        paginated = self.paginated_result(result, method='POST', url=api_url, json=payload)
        yield from formatter(paginated, key='Ads')

    @gateway_retry(retry_codes=[52, 1000, 1001, 1002])
    def get_sitelinks(self, selection_criteria,
                      field_names=constants.YD_SITELINKS_COLLECTION_FIELDNAMES) -> GeneratorType:
        """"""
        api_url = f'{self.get_api_url()}/{self.endpoints.SITELINKS}'
        payload = {
            'method': 'get',
            'params': {
                'SelectionCriteria': selection_criteria,
                'FieldNames': field_names,
            }
        }
        response = self.client.send(method='POST', url=api_url, json=payload)
        result = self.get_response_result(response.result().data)
        paginated = self.paginated_result(result, method='POST', url=api_url, json=payload)
        yield from formatter(paginated, key='SitelinksSets')


class OAuthGateway(AuthorizableGateway):
    """
    Oauth authorization gateway.
    Here we implement methods of Yandex Oauth API.
    """

    client = YandexOauthClient()
    token_field_name = constants.YD_OAUTH_TOKEN_FIELD_NAME  # This lets client change this attr dynamically.

    def get_oauth_token(self, url, **params) -> str:
        """
        Get authorization token from Yandex direct API.
        More info on Oauth process `here <https://tech.yandex.com/oauth/doc/dg/reference/auto-code-client-docpage/>`_.

        Client must provide at least {'grant_type': 'authorization_code', 'code': 'access_code'} as other params
        included in token request (CLIENT_ID, CLIENT_SECRET) are inserted dynamically in GatewayClient and defined
        in app settings (usually, though, in ENV variables).

        :param url:         authorization api entry point
        :type url:          str
        :param params:      token request params
        :type params:       dict
        :rtype:             str
        :return:            Yandex Direct API oauth token
        :raises:            UnExpectedResult if no token data received
        """
        response = self.client.send(method='POST', url=url, data=params)
        result = response.result().data
        token = result.get(self.token_field_name)
        if not token:
            raise UnExpectedResult(result)
        return token
