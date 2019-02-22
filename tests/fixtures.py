import json

import pytest
from django_celery_results.models import TaskResult

from auctioneer.models import KeywordBidRule
from common.account import controllers
from common.http import gateway, client


@pytest.fixture
def http_client():
    return client.GatewayHttpClient()


@pytest.fixture()
def async_http_client():
    return client.AsyncGatewayHttpClient()


@pytest.fixture
def yd_client():
    return client.YandexDirectClient()


@pytest.fixture
def oauth_client():
    return client.YandexOauthClient()


@pytest.fixture
def yd_gateway():
    return gateway.YandexDirectGateway(token='AQAAAAAmDYi1AARfvcIWFiq_qktKi-_qoybPSf4')


@pytest.fixture
def oauth_gateway():
    return gateway.OAuthGateway(client_id='123', client_secret='321')


@pytest.fixture
def account(db):
    return controllers.create_account_with_login('test_account')


@pytest.fixture
def json_from_path():
    def wrapper(path:str):
        with open(path) as f:
            return json.loads(f.read())
    return wrapper

@pytest.fixture
def keyword_bids(json_from_path):
    return json_from_path('tests/tests_data/keyword_bids_test.json')


@pytest.fixture
def keyword_bids_w_warnings(json_from_path):
    return json_from_path('tests/tests_data/set_kw_bids_with_warnings.json')


@pytest.fixture
def ads(json_from_path):
    return json_from_path('tests/tests_data/ads.json')

@pytest.fixture()
def kwb_rule(account, db):
    return KeywordBidRule.objects.create(**{
        'title': 'SomeRule',
        'account': account,
        'target_type': 1,
        'target_values': [1, 2, 3],
        'target_bid_diff': 10,
        'bid_increase_percentage': 10,
        'max_bid': 10
    })


@pytest.fixture
def task_result(db, keyword_bids_w_warnings):
    return TaskResult.objects.create(task_id=1, status='SUCCESS', result=json.dumps(
        keyword_bids_w_warnings['result']['SetResults']))