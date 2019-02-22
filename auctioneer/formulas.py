"""
A collection of keyword bid calcualation formulas.
Basically, here the part of main business logic domain is collected.

Implementing formulas you may add new calculation rules and extend existing rules.
In general, Formulas should be applied through :py:mod:auctioneer.controllers.bid_calculator.
Bid calculator should import formulas modules and use them to calculate bids.
Using formulas directly is possible, but not adviced as it will couple client code to particular formula
implementation.

"""

from . import entities


class KeywordBidFormula:
    """
    Rule application formula abstract class.
    Subclasses should implement how rule will be applied to entity in apply() method
    Formula is used to mutate KeywordBid. It uses KeywordBid rule as a source of parameters
    and implements logic in which that parameters should be used.

    Formula can be applied as function call or direct method apply() call::

        formula = KeywordBidFormula(kw_bid, kw_bid_rule)
        formula(*args, **kwargs)        # function formula application
        formula.apply(*args, **kwargs)  # method call formula application

    """
    def __init__(self, keyword_bid: entities.KeywordBid, rule: entities.KeywordBidRule):
        """
        :param keyword_bid:         keyword bid **entity**
        :param rule:                keyword bid **entity**
        :type keyword_bid:          entities.KeywordBid
        :type rule:                 entities.KeywordBidRule
        """
        assert type(keyword_bid) is entities.KeywordBid, f'Expected {entities.KeywordBid} got {type(keyword_bid)}'
        assert type(rule) is entities.KeywordBidRule, f'Expected {entities.KeywordBidRule} got {type(rule)}'
        self.keyword_bid = keyword_bid
        self.rule = rule

    def apply(self, *args, **kwargs) -> entities.KeywordBid:
        """
        Use keyword bid rule data to apply formula to given entity.

        Subclasses should implement main formula logic here

        :rtype:         entities.KeywordBid
        :return:        Altered Keyword bid entity with applied formula results
        """
        raise NotImplementedError

    def __call__(self, *args, **kwargs) -> entities.KeywordBid:
        return self.apply(*args, **kwargs)


class SearchBidFormula(KeywordBidFormula):
    """
    Search Bid calculation algorithm.
    Calculates new search bid that should be set on a given keyword
    """
    def apply(self, *args, **kwargs):
        """
        More info on calculation algorithm `here <https://jira.lamoda.ru/browse/MARK-455>`_.
        """
        auction_bids = self.keyword_bid.search.get('AuctionBids')
        if not auction_bids:
            return self.keyword_bid
        first_bid, second_bid = map(lambda bid_item: bid_item.get('Bid'), auction_bids.get('AuctionBidItems')[:2])
        bid_diff = (first_bid - second_bid) / second_bid
        target_bid = min(
            (first_bid if bid_diff < self.rule.target_bid_diff else second_bid) *
            (1 + self.rule.bid_increase_percentage),
            self.rule.max_bid)
        self.keyword_bid.search['Bid'] = int(target_bid)
        return self.keyword_bid
