"""
Auctioneer controller.
Here we should implement main login of auctioneer app.
"""
from auctioneer import controllers
from common.account import controllers as account


class NoResponseError(Exception):
    """"""


def run(kw_bid_rule_id: int):
    kw_bid_rule = controllers.keyword_bid_rule.get_keywordbid_rule(kw_bid_rule_id)
    assert kw_bid_rule, 'No keyword bid rule found.'  # this is here to break gracefuly
    kw_bid_rule_entity = controllers.keyword_bid_rule.map_keyword_bid_rule(kw_bid_rule)
    gateway = account.make_yd_gateway(kw_bid_rule_entity.account)
    params = {'selection_criteria': {kw_bid_rule_entity.target_type: kw_bid_rule_entity.target_values}}
    response = controllers.keyword_bids.calculate_keyword_bids(gateway, kw_bid_rule_entity, **params)
    if not response:
        raise NoResponseError('No response recieved')
    return response
