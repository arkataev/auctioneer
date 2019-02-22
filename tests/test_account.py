from auctioneer import models
from common.account import controllers as account


def test_account_create(db):
    acc = account.create_account_with_login('test_login')
    assert isinstance(acc, models.Account)
    assert acc.login == 'test_login'
    assert acc.token is None


def test_set_account_token(db):
    set_token = account.set_account_token
    acc = account.create_account_with_login('test_login')
    set_token(acc.id, 'some_token')
    assert not acc.enabled
    acc.refresh_from_db()
    assert acc.token == 'some_token'
    assert acc.enabled
    set_token(acc.id, 'some_new_token')
    acc.refresh_from_db()
    assert acc.token == 'some_token'
    set_token(acc.id, 'some_new_token', force=True)
    acc.refresh_from_db()
    assert acc.token == 'some_new_token'


def test_make_yd_gateway_for_account(db):
    set_token = account.set_account_token
    acc = account.create_account_with_login('test_login')
    set_token(acc.id, 'some_token')
    acc.refresh_from_db()
    gw = account.make_yd_gateway(acc.id)
    assert isinstance(gw, account.YandexDirectGateway)
    assert acc.token == gw.client.auth_data._token
