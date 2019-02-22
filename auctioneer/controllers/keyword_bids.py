"""
Controller for keyword bids set and retrieval.

Essentially auctioneer runs the three step cycle: get-calculate-set. It retrieves keywordbids data from
Yandex Direct API, recalculates keyword bids with the given rules and sends new keyword bids to YD API.

"""
import logging

from types import GeneratorType
from typing import Iterator

from common import http, utils
from . import bid_calculator
from .. import entities

_logger = logging.getLogger(__name__)


def map_keyword_bids(kw_bid_data: GeneratorType) -> [entities.KeywordBid]:
    """
    Create multiple KeywordBid entites from data.

    This will create a generator which will yield :py:class:`auctioneer.entities.KeywordBid`,
    filled with data provided. Data should comply to Yandex Direct API
    `keyword_bids.get <https://tech.yandex.ru/direct/doc/ref-v5/keywordbids/get-docpage/>`_ response structure::

        [
        {'KeywordBids': [{
            'CampaignId': 123,
            'AdGroupId': 123,
            'KeywordId': 123,
            'ServingStatus': 'some status',
            'StrategyPriority': 'priority',
            'Search': {
                'Bid': 123,
                'AuctionBids': {'AuctionBidItems': [{'TrafficVolume': 1, 'Bid': 1000, 'Price': 1000}]}
            ...}],
        {'KeywordBids': ... }
        ...
        ]

    :param kw_bid_data:     a collection of dictionaries with keyword bids data
    :type kw_bid_data:      GeneratorType
    :return:                a generator of keyword bids entities
    :rtype:                 Iterator[KeywordBid]
    """
    for item in kw_bid_data:
        try:
            entity = entities.KeywordBid(**{utils.camel_to_snake(k): v for k, v in item.items()})
        except (ValueError, AttributeError, TypeError):
            raise http.UnExpectedResult(f'Unexpected keyword bids data {item}')
        yield entity


def get_keyword_bids(gateway: http.YandexDirectGateway, **kwargs) -> Iterator[entities.KeywordBid]:
    """
    Load all keyword bids for given params from yandex direct gateway and map data
    to :py:class:`auctioneer.entities.KeywordBid`.
    This will use provided gateway to request keyword bids data from yandex direct API::

        account_id = keyword_bid_rule = 1
        kwb_rule = ctrl.keyword_bid_rule.get_keywordbid_rule(keyword_bid_rule)
        gateway = ctrl.accounts.make_yd_gateway_for_account(account_id)
        kwb_selection_criteria = {'KeywordIds': [1,2,3]}  # which keywords to retrieve from Yandex Direct
        keyword_bids = ctrl.keyword_bids.get_keyword_bids(gateway, **kwb_selection_criteria)

    :param gateway:         gateway instance
    :type gateway:          YandexDirectGateway
    :return:                generator of keyword bids entities
    :rtype:                 [entities.KeywordBid]
    """
    yield from map_keyword_bids(gateway.keyword_bids_gen(**kwargs))


def set_keyword_bids(gateway: http.YandexDirectGateway, keyword_bids: [entities.KeywordBid]) -> Iterator[dict]:
    """
    Send data to Yandex direct gateway to set keyword bids.

    :param gateway:         gateway instance
    :param keyword_bids:    a collection of :py:class:`auctioneer.entities.KeywordBid`
    :type gateway:          YandexDirectGateway
    :type keyword_bids:     iter
    :rtype:                 Iterator[dict]
    :return:                Iterator of dictionaries with `Yandex Direct response data \
    <https://tech.yandex.ru/direct/doc/ref-v5/keywordbids/set-docpage/>`_

    """
    data = [{'KeywordId': kw_bid.keyword_id, 'SearchBid': kw_bid.search.get('Bid')} for kw_bid in keyword_bids]
    yield from gateway.set_keyword_bids(data)


def calculate_keyword_bids(gateway: http.YandexDirectGateway, kw_bid_rule: entities.KeywordBidRule, **params) -> list:
    """
    Recalculate bids for a given rule.

    Essentially this is the **key apllication function**. It wraps main logic of get-calculate-set cycle.

    :param gateway:         gateway instance
    :param kw_bid_rule:     rule instance to apply to keyword bids
    :param params:          additional params. Mainly these are params for retrieving keyword bids from YD API
    :type gateway:          YandexDirectGateway
    :type kw_bid_rule:      entities.KeywordBidRule
    :type params:           dict
    :rtype:                 dict
    :return:                dictionary with `Yandex Direct response data \
    <https://tech.yandex.ru/direct/doc/ref-v5/keywordbids/set-docpage/>`_
    """
    # recieve keyword bids from yandex direct
    kw_bids_gen = get_keyword_bids(gateway, **params)
    # apply calculation formulas to each keyword bid
    kw_bids = bid_calculator.apply_bid_rule(kw_bid_rule, kw_bids_gen)
    # send keyword bids to yandex direct api
    response = list(set_keyword_bids(gateway, kw_bids))
    return response
