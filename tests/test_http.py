import json
import time

import pytest
import requests
import responses

from common.http import exceptions

from common.http.oauth import YandexDirectAuth

TEST_URL = 'https://httpbin.org/'


def test_paginated_result(yd_gateway):
    url = f'{yd_gateway.get_api_url()}/{yd_gateway.endpoints.KEYWORD_BIDS}'
    with responses.RequestsMock() as mock:
        mock.add(method=mock.POST, url=url, status=200, json={'result': {'LimitedBy': 10000}})
        mock.add(method=mock.POST, url=url, status=200, json={'result': {'LimitedBy': 100}})
        mock.add(method=mock.POST, url=url, status=200, json={'result': {'LimitedBy': 10}})
        mock.add(method=mock.POST, url=url, status=200, json={'result': 'OK'})
        r = yd_gateway.keyword_bids_gen(selection_criteria={"CampaignIds": []})
        assert {'LimitedBy': 10000} == next(r)
        assert {'LimitedBy': 100} == next(r)
        assert {'LimitedBy': 10} == next(r)
        assert "OK" == next(r)


def test_gateway_retry(yd_gateway):
    url = f'{yd_gateway.get_api_url()}/{yd_gateway.endpoints.KEYWORD_BIDS}'
    with responses.RequestsMock() as mock:
        mock.add(method=mock.POST, url=url, status=200, json={'result': {'error_code': 1001}})
        mock.add(method=mock.POST, url=url, status=200, json={'result': {'error_code': 1001}})
        mock.add(method=mock.POST, url=url, status=200, json={'result': {'error_code': 1001}})
        mock.add(method=mock.POST, url=url, status=200, json={'result': 'OK'})
        r = yd_gateway.keyword_bids_gen(selection_criteria={"CampaignIds": []})
        assert next(r) == 'OK'


def test_gateway_max_retry_error(yd_gateway):
    url = f'{yd_gateway.get_api_url()}/{yd_gateway.endpoints.KEYWORD_BIDS}'
    with responses.RequestsMock() as mock:
        mock.add(method=mock.POST, url=url, status=200, json={'result': {'error_code': 1001}})
        mock.add(method=mock.POST, url=url, status=200, json={'result': {'error_code': 1001}})
        mock.add(method=mock.POST, url=url, status=200, json={'result': {'error_code': 1001}})
        mock.add(method=mock.POST, url=url, status=200, json={'result': {'error_code': 1001}})
        r = yd_gateway.keyword_bids_gen(selection_criteria={"CampaignIds": []})
        with pytest.raises(exceptions.MaxRetry):
            next(r)


def test_http_init(http_client):
    assert http_client.configured
    assert http_client.DEFAULT_CONFIG
    http_client.configure(hello='world')
    assert 'hello' not in http_client.DEFAULT_CONFIG
    assert 'hello' in http_client._config


def test_prepare_request(http_client):
    with pytest.raises(exceptions.PayloadError):
        http_client._prepare_request(hello='world')
    with pytest.raises(exceptions.PayloadError):
        http_client._prepare_request(method='foo')
    with pytest.raises(exceptions.PayloadError):
        http_client._prepare_request(method='GET', url='bar')
    with pytest.raises(exceptions.PayloadError):
        http_client._prepare_request(method='GET', url='https://google.com', abc='24324')
    http_client.headers = {'abc': 123}
    with pytest.raises(exceptions.PayloadError):
        http_client._prepare_request(method='POST', url='https://google.com', json={'a': 1})
    http_client.headers = {'hello': 'world'}
    prepared = http_client._prepare_request(method='POST', url='https://google.com', json={'a': 1})
    assert type(prepared) is requests.PreparedRequest
    assert prepared.body == json.dumps({'a': 1}).encode()
    assert prepared.headers['Content-Type'] == 'application/json'
    assert 'hello' in prepared.headers


def test__make_payload(http_client):
    with pytest.raises(exceptions.PayloadError):
        http_client._make_payload(hello='foo', world='bar')
    method, url, other = http_client._make_payload(method='GET', url='http://helloworld.com',
                                                   params={'hello': 'world'})
    assert method == 'GET'
    assert url == 'http://helloworld.com'
    assert other['params'] == {'hello': 'world'}


def test_set_retry_policy(http_client):
    with pytest.raises(exceptions.ConfigError):
        http_client.set_retry_policy('hello')
    http_client.set_retry_policy(3)
    assert http_client._retry_policy == 3


def test_yd_init(yd_client):
    assert not yd_client.configured


def test_send_async(async_http_client):
    url = 'http://hello.world'
    with responses.RequestsMock() as mock:
        response = {'method': mock.POST, 'url': url, 'status': 200, 'body': 'hello'}
        mock.add(**response)
        mock.add(**response)
        mock.add(**response)
        buf_id = async_http_client.get_pool_id()
        request = {'method': 'POST', 'url': url, 'json': {'hello:': 'world'}}
        async_http_client.pool_send(buf_id, **request)
        async_http_client.pool_send(buf_id, **request)
        async_http_client.pool_send(buf_id, **request)
        for result, payload in async_http_client.pool_receive(buf_id):
            assert result.result().data == 'hello'
            assert payload == request


def _test_send_async_time(async_http_client):
    url = 'http://httpbin.org/post'
    request = {'method': 'POST', 'url': url, 'json': {'hello:': 'world'}}
    buf_id = async_http_client.get_pool_id()
    start = time.time()
    for _ in range(100):
        async_http_client.pool_send(buf_id, **request)
    results = [r.result().data for r, _ in async_http_client.pool_receive(buf_id)]
    end = time.time()
    assert len(results) == 100
    print(end - start)


def test_set_auth_data_yd(yd_client):
    with pytest.raises(exceptions.ConfigError):
        yd_client.set_auth_data(hello='world')
    yd_client.set_auth_data(token='123')
    assert yd_client.authorized
    assert type(yd_client.auth_data) is YandexDirectAuth
    assert yd_client.auth_data._token == '123'


def test_prepare_yd_request(yd_client):
    yd_client.set_auth_data(token='123')
    prep = yd_client._prepare_request(method="GET", url='https://google.com', params={'a': 1})
    assert 'Authorization' in prep.headers
    assert prep.headers['Authorization'] == 'Bearer 123'
    assert 'a=1' in prep.url
    prep = yd_client._prepare_request(method="POST", url='https://google.com', json={'a': 1})
    assert json.loads(prep.body) == {'a': 1}


def test_ouath_payload(oauth_client):
    oauth_client.set_auth_data(client_id=123, token='123', client_secret=123)
    assert oauth_client.auth_data() == {'client_id': 123, 'client_secret': 123}
    method, url, other = oauth_client._make_payload(method='POST', url='http://helloworld.com', data={})
    assert other['data'] == oauth_client.auth_data()
    prep = oauth_client._prepare_request(method='POST', url='http://helloworld.com', data={})
    assert prep.headers['Content-Type'] == 'application/x-www-form-urlencoded'
    assert 'client_id' in prep.body
    assert 'client_secret' in prep.body


def test_get_keyword_bids(yd_gateway, keyword_bids):
    url = f'{yd_gateway.get_api_url()}/{yd_gateway.endpoints.KEYWORD_BIDS}'
    data = keyword_bids
    with responses.RequestsMock() as mock:
        mock.add(method='POST', url=url, status=200, json=data)
        mock.add(method='POST', url=url, status=200, json=data)
        mock.add(method='POST', url=url, status=200, json=data)
        response = yd_gateway.keyword_bids_gen(selection_criteria={"CampaignIds": list(range(10))})
        kwb = list(response)
        assert len(kwb) == 2
        assert 'CampaignId' in kwb[0]
        response = yd_gateway.keyword_bids_gen(selection_criteria={"CampaignIds": list(range(20))})
        kwb = list(response)
        assert len(kwb) == 4
        assert 'CampaignId' in kwb[0]


def test_set_keywordbid(yd_gateway, keyword_bids_w_warnings):
    url = f'{yd_gateway.get_api_url()}/{yd_gateway.endpoints.KEYWORD_BIDS}'
    data = keyword_bids_w_warnings
    with responses.RequestsMock() as mock:
        mock.add(method='POST', url=url, status=200, json=data)
        mock.add(method='POST', url=url, status=200, json=data)
        mock.add(method='POST', url=url, status=200, json=data)
        response = yd_gateway.set_keyword_bids(list(range(1000)))
        results = list(response)
        assert len(results) == 1514
        assert 'Warnings' in results[0]
        assert 'KeywordId' in results[6]
        response = yd_gateway.set_keyword_bids(list(range(20_000)))
        results = list(response)
        assert len(results) == 1514 * 2
        assert 'Warnings' in results[0]
        assert 'KeywordId' in results[6]


def test_get_client_login(yd_gateway):
    url = f'{yd_gateway.get_api_url()}/{yd_gateway.endpoints.CLIENTS}'
    with responses.RequestsMock() as mock:
        mock.add(method='POST', url=url, status=200, json={"result": {"Clients": [{"Login": "sem-test-lamoda"}]}})
        mock.add(method='POST', url=url, status=200, json={"result": {"Clients": []}})
        mock.add(method='POST', url=url, status=200, json={"result": {"Clients": [{'Error': 'oopps!'}]}})
        mock.add(method='POST', url=url, status=200, body='ooops!')
        login = yd_gateway.get_client_login()
        assert login == 'sem-test-lamoda'
        with pytest.raises(exceptions.UnExpectedResult):
            yd_gateway.get_client_login()
        with pytest.raises(exceptions.UnExpectedResult):
            yd_gateway.get_client_login()
        with pytest.raises(exceptions.UnExpectedResult):
            yd_gateway.get_client_login()


def test_get_campaings(yd_gateway):
    url = f'{yd_gateway.get_api_url()}/{yd_gateway.endpoints.CAMPAIGNS}'
    with responses.RequestsMock() as mock:
        mock.add(method=mock.POST, url=url, status=200, json={'result': {'LimitedBy': 10000}})
        mock.add(method=mock.POST, url=url, status=200, json={'result': {'LimitedBy': 100}})
        mock.add(method=mock.POST, url=url, status=200, json={'result': {'LimitedBy': 10}})
        mock.add(method=mock.POST, url=url, status=200, json={'result': 'OK'})
        camps = yd_gateway.get_campaigns(selection_criteria={'Ids': []})
        assert next(camps) == {'LimitedBy': 10000}
        assert next(camps) == {'LimitedBy': 100}
        assert next(camps) == {'LimitedBy': 10}
        assert next(camps) == "OK"
    # test web-response
    # yd_gateway.client.set_auth_data(token='AQAAAAAmU7wjAAJymiZdgSjHnUwjlUIH_Wkol8A')
    # camps = yd_gateway.get_campaigns(selection_criteria={'Ids':[39192706, 34723822, 34723829, 34724306]})
    # assert next(camps).get('Id') == 34723822


def test_get_ads(yd_gateway, ads):
    url = f'{yd_gateway.get_api_url()}/{yd_gateway.endpoints.ADS}'
    data = ads
    with responses.RequestsMock() as mock:
        mock.add(method=mock.POST, url=url, status=200, json={'result': {'LimitedBy': 10000}})
        mock.add(method=mock.POST, url=url, status=200, json={'result': {'LimitedBy': 100}})
        mock.add(method=mock.POST, url=url, status=200, json={'result': {'LimitedBy': 10}})
        mock.add(method=mock.POST, url=url, status=200, json=data)
        _ads = yd_gateway.get_ads(selection_criteria={"CampaignIds": []})
        assert next(_ads) == {'LimitedBy': 10000}
        assert next(_ads) == {'LimitedBy': 100}
        assert next(_ads) == {'LimitedBy': 10}
        assert next(_ads).get('Id') == 5709812713
    # test web-response
    # ads = yd_gateway.get_ads(
    #     selection_criteria={"CampaignIds": [39192706,34723822, 34723829, 34724306]},
    #     **{
    #         'text_ad_field_names': ['Href', 'SitelinkSetId'],
    #         'text_image_ad_field_names': ['Href'],
    #         'dynamic_text_ad_field_names': ['SitelinkSetId'],
    #         'mobile_app_image_ad_field_names': ['TrackingUrl'],
    #         'mobile_app_ad_field_names': ['TrackingUrl']
    #     })
    # assert next(ads).get('Id') == 5709812713
    # yd_gateway.client.set_auth_data(token='AQAAAAAmU7wjAAJymiZdgSjHnUwjlUIH_Wkol8A')


def test_get_sitelinks(yd_gateway):
    url = f'{yd_gateway.get_api_url()}/{yd_gateway.endpoints.SITELINKS}'
    with responses.RequestsMock() as mock:
        mock.add(method=mock.POST, url=url, status=200, json={'result': {'LimitedBy': 10000}})
        mock.add(method=mock.POST, url=url, status=200, json={'result': {'LimitedBy': 100}})
        mock.add(method=mock.POST, url=url, status=200, json={'result': {'LimitedBy': 10}})
        mock.add(method=mock.POST, url=url, status=200, body=b"OK")
        sitelinks = yd_gateway.get_sitelinks(selection_criteria={"Ids": []})
        assert next(sitelinks) == {'LimitedBy': 10000}
        assert next(sitelinks) == {'LimitedBy': 100}
        assert next(sitelinks) == {'LimitedBy': 10}
        assert next(sitelinks) == "OK"
    # test web-response
    # yd_gateway.client.set_auth_data(token='AQAAAAAmU7wjAAJymiZdgSjHnUwjlUIH_Wkol8A')
    # sitelinks = yd_gateway.get_sitelinks(selection_criteria={"Ids": [799663215, 799658424]})
    # assert next(sitelinks).get('Id') == 799658424


def test_get_oauth_token(oauth_gateway):
    with responses.RequestsMock() as mock:
        mock.add(method=mock.POST, url='http://auth.url', status=200, json={
            "access_token": "AQAAAAAvQzzuAARfvaWKigBvLE1ljgH0XBHIuIA",
        })
        mock.add(method=mock.POST, url='http://auth.url', status=200, json={
            "token": "AQAAAAAvQzzuAARfvaWKigBvLE1ljgH0XBHIuIA",
        })
        token = oauth_gateway.get_oauth_token(url='http://auth.url')
        assert oauth_gateway.client.auth_data() == {'client_id': '123', 'client_secret': '321'}
        assert token == "AQAAAAAvQzzuAARfvaWKigBvLE1ljgH0XBHIuIA"
        with pytest.raises(exceptions.UnExpectedResult):
            oauth_gateway.get_oauth_token(url='http://auth.url')
