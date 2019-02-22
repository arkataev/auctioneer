"""
Main controllers that is used to calculate and set new bids using calculation rules and formulas.

What Rule is?
=============

The keyword bid calculation rule :py:class:`auctioneer.entities.KeywordBidRule` is the main entity that
represents user-defined parameters that are used in keyword bid calculation formulas.

What Formula is?
================

The keyword bid calculation formula :py:class:`auctioneer.formulas.KeywordBidFormula` represents the main
logic according to which keyword bids are calculated. Parameters defined in Rules are than applied to one or
multiple formulas with target keyword bid.

"""

from functools import reduce, partial
from types import GeneratorType
from typing import Iterator
from .. import formulas, entities

# formulas will be applied in order
BID_CALCULATION_FORMULAS = (
    formulas.SearchBidFormula,
)


def apply_bid_rule(kw_bid_rule: entities.KeywordBidRule, kw_bids: Iterator[entities.KeywordBid],
                   formulas_collection: tuple=BID_CALCULATION_FORMULAS) -> iter:
    """
    Apply calculation formulas to multiple keyword bids

    .. code-block:: python

            # Get keyword bid rule
            # While there are keyword bids:
            #    Get keyword bid
            #    While there are fomulas:
            #        Get formula
            #       Apply formula with given keyword bid rule to current keyword bid

            from auctioneer import controllers as ctrl

            account_id = keyword_bid_rule = 1
            kwb_rule = ctrl.keyword_bid_rule.get_keywordbid_rule(keyword_bid_rule)
            gateway = ctrl.accounts.make_yd_gateway_for_account(account_id)
            kwb_selection_criteria = {'KeywordIds': [1,2,3]}  # which keywords to retrieve from Yandex Direct
            keyword_bids = ctrl.keyword_bids.get_keyword_bids(gateway, **kwb_selection_criteria)
            calculated = apply_bid_rule(kwb_rule, keyword_bids)


    This method is used to apply in chain multiple formulas with given params to a number of keyword bids.
    Each formula uses the same keyword bid rule calculation params.

    :param kw_bid_rule:             a rule parameters to use in formulas
    :param kw_bids:                 keyword bids entities
    :param formulas_collection:     formulas to apply to each keyword bid. Will be applied in order
    :type kw_bid_rule:              entities.KeywordBidRule
    :type kw_bids:                  GeneratorType
    :type formulas_collection:      tuple
    :rtype:                         iter
    :return:                        processed keyword bids
    """
    calculate = partial(_chain_apply, rule=kw_bid_rule, formulas_collection=formulas_collection)
    kw_bids_calculated = map(calculate, kw_bids)
    return kw_bids_calculated


def _chain_apply(keyword_bid: entities.KeywordBid,
                 rule: entities.KeywordBidRule,
                 formulas_collection: [formulas.KeywordBidFormula]) -> entities.KeywordBid:
    """
    Apply calculation formulas to keyword bid in chain.
    Result of every calculation is passed to next formula
    """
    result = reduce(lambda kw, formula: formula(kw, rule).apply(), formulas_collection, keyword_bid)
    return result
