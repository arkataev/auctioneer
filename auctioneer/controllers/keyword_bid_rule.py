"""
Controllers for keyword bid rules set and retrieval
"""

from .. import models, entities


def get_keywordbid_rule(kw_bid_rule_id: int) -> models.KeywordBidRule or None:
    """
    Get KeywordBid model by id

    This function returns a data source for creating Keyword Bid Rule (KBR), though to be precise,
    this should have been implemented as a gateway. But for the sake of simplicity this logic implemented
    in controller directly

    :param kw_bid_rule_id:      id of keyword bid rule stored in DB
    :type kw_bid_rule_id:       int
    :returns:                   KeywordBidRule model if model exists
    :returns:                   None if model does not exist
    :rtype:                     django.db.models.KeywordBidRule or None
    """
    try:
        kw_bid_rule_model = models.KeywordBidRule.objects.select_related('account').get(id=kw_bid_rule_id)
    except models.KeywordBidRule.DoesNotExist:
        return None
    else:
        return kw_bid_rule_model


def map_keyword_bid_rule(kw_bid_rule_model: models.KeywordBidRule) -> entities.KeywordBidRule:
    """
    Map data to entity. This will create an entity from data source.

    :param kw_bid_rule_model:           data source to get data from to fill the entity
    :type kw_bid_rule_model:            django.db.models.KeywordBidRule
    :return:                            KeywordBidRule entity filled with data
    :rtype:                             entities.KeywordBidRule
    """
    data = {
        'account': kw_bid_rule_model.account.id,
        'target_type': kw_bid_rule_model.get_target_type_display(),
        'target_values': kw_bid_rule_model.target_values,
        'target_bid_diff': kw_bid_rule_model.get_target_bid_diff_display(),
        'bid_increase_percentage': kw_bid_rule_model.get_bid_increase_percentage_display(),
        'max_bid': kw_bid_rule_model.get_max_bid_display()
    }
    return entities.KeywordBidRule(**data)
