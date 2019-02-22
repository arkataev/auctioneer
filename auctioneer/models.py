"""
A collection of django-models implementations. Models here are data sources, not a business entities.
Avoid using them directly in application's business logic.
Model management logic implemented in :py:mod:`auctioneer.controllers`
"""

import logging

from django.contrib.postgres.fields import ArrayField
from django.db import models

from common.account.models import Account
from . import constants

_logger = logging.getLogger('auctioneer.models')


class KeywordBidRule(models.Model):
    """
    Yandex Direct keyword bids calculation rule data source.
    """
    title = models.CharField(max_length=100)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    """
    Each rule relates to one given account
    """
    target_type = models.IntegerField(choices=constants.KEYWORD_BID_TARGET_TYPES, verbose_name='Target Type')
    """
    To which types of Yandex Direct bid entities rule should be applied. 
    This can be Campaign | AdGroup | Keyword.
    """
    target_values = ArrayField(models.BigIntegerField(), verbose_name='Target Values', max_length=10)
    """
    Yandex Direct Ids of chosen target types. For what Ids should the bid be changed.
    """
    target_bid_diff = models.IntegerField(verbose_name='Target bid diff (%)')
    """
    A difference in percents between the bid for the first maximum forecasted amount and 
    the bid for the second maximum forecasted amount 
    """
    bid_increase_percentage = models.IntegerField(verbose_name='Bid increase (%)')
    """
    To what rate should our bid be risen. 
    """
    max_bid = models.IntegerField(verbose_name='Max bid limit (RUB)')
    """
    Upper threshold for our bid increase
    """

    class Meta:
        verbose_name = 'Keyword Rule'
        verbose_name_plural = "Keyword Rules"

    def get_max_bid_display(self):
        """
        User sets this value as small int. But Yandex Direct operates with values divisible by 1 000 000
        :return:    max bid value multiplyed by 1 000 000
        """
        return self.max_bid * 1_000_000

    def get_bid_increase_percentage_display(self):
        """
        User sets this value as small int. But calculation formulas operates with percents
        :return:        bid increase rate in percents
        """
        return self.bid_increase_percentage / 100

    def get_target_bid_diff_display(self):
        """
        User sets this value as small int. But calculation formulas operates with percents
        :return:        target bid difference in percents
        """
        return self.target_bid_diff / 100

    def __str__(self):
        return self.title
