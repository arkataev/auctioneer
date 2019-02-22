import pytest
import responses

from auctioneer import constants, controllers, entities
from common.http import UnExpectedResult


def test_keywordbid_rule_init(kwb_rule, account):
    assert kwb_rule.get_max_bid_display() == kwb_rule.max_bid * 1_000_000
    assert kwb_rule.get_bid_increase_percentage_display() == kwb_rule.bid_increase_percentage / 100
    assert kwb_rule.get_target_bid_diff_display() == kwb_rule.target_bid_diff / 100
    assert kwb_rule.account is account
    assert kwb_rule.target_values == [1,2,3]
    assert kwb_rule.get_target_type_display() in map(lambda t: t[1], constants.KEYWORD_BID_TARGET_TYPES)


def test_make_keywordbid_rule(kwb_rule):
    kw_bid_rule = controllers.keyword_bid_rule.get_keywordbid_rule(kwb_rule.id)
    assert kwb_rule == kw_bid_rule
    assert kw_bid_rule.account == kwb_rule.account
    not_found_kwb_rule = controllers.keyword_bid_rule.get_keywordbid_rule(0)
    assert not_found_kwb_rule is None


def test_map_keywordbid_rule(kwb_rule, account):
    kwb_ent = controllers.keyword_bid_rule.map_keyword_bid_rule(kwb_rule)
    assert isinstance(kwb_ent, entities.KeywordBidRule)
    assert kwb_ent.account == account.id
    for f in kwb_rule._meta.fields:
        if f.name in ('id', 'title') :
            continue
        model_attr = getattr(kwb_rule, f.name)
        ent_attr = getattr(kwb_ent, f.name)
        if not hasattr(model_attr, 'pk'):
            try:
                assert ent_attr == getattr(kwb_rule, f'get_{f.name}_display')()
            except AttributeError:
                assert ent_attr == model_attr
        else:
            assert ent_attr == model_attr.id


def test_get_keyword_bids(yd_gateway, keyword_bids):
    url = f'{yd_gateway.get_api_url()}/{yd_gateway.endpoints.KEYWORD_BIDS}'
    data = keyword_bids
    with responses.RequestsMock() as mock:
        mock.add(method='POST', url=url, status=200, json=data)
        mock.add(method='POST', url=url, status=404)
        mock.add(method='POST', url=url, status=200, json=data)
        kwb = controllers.keyword_bids.get_keyword_bids(yd_gateway, selection_criteria={"CampaignIds": []})
        assert next(kwb).keyword_id == 13102117581
        assert next(kwb).keyword_id == 13102117582
        kwb = controllers.keyword_bids.get_keyword_bids(yd_gateway, selection_criteria={"CampaignIds": []})
        with pytest.raises(UnExpectedResult):
            next(kwb)
        kwb = controllers.keyword_bids.get_keyword_bids(yd_gateway, selection_criteria={"CampaignIds": []})
        assert type(next(kwb).as_dict()) is dict


def test_set_keyword_bids(yd_gateway, keyword_bids, keyword_bids_w_warnings):
    url = f'{yd_gateway.get_api_url()}/{yd_gateway.endpoints.KEYWORD_BIDS}'
    kwb = controllers.keyword_bids.map_keyword_bids(keyword_bids['result']['KeywordBids'])
    with responses.RequestsMock() as mock:
        mock.add(method='POST', url=url, status=200, json=keyword_bids_w_warnings)
        response = controllers.keyword_bids.set_keyword_bids(yd_gateway, kwb)
        assert len(list(response)) == 1514


def test_calculate_keyword_bids(yd_gateway, kwb_rule, keyword_bids, keyword_bids_w_warnings):
    url = f'{yd_gateway.get_api_url()}/{yd_gateway.endpoints.KEYWORD_BIDS}'
    kwb_ent = controllers.keyword_bid_rule.map_keyword_bid_rule(kwb_rule)
    with responses.RequestsMock() as mock:
        mock.add(method='POST', url=url, status=200, json=keyword_bids)
        mock.add(method='POST', url=url, status=200, json=keyword_bids_w_warnings)
        mock.add(method='POST', url=url, status=200, json={'error': {'error_code': 0000, 'error_message': 'oops!'}})
        result = controllers.keyword_bids.calculate_keyword_bids(yd_gateway, kwb_ent,
                                                                 selection_criteria={"CampaignIds": []})
        assert len(result) == 1514
        with pytest.raises(UnExpectedResult):
            controllers.keyword_bids.calculate_keyword_bids(yd_gateway, kwb_ent,
                                                            selection_criteria={"CampaignIds": []})

