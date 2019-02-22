from django.db import models
from . import costants as const


class Account(models.Model):
    """
    Yandex Direct account data.

    This model stores main data of Yandex Direct user account.
    Account management is implemented in :py:mod:`auctioneer.conteller.account`. module
    """
    login = models.CharField(max_length=50, verbose_name='Yandex Direct Login', unique=True)
    token = models.CharField(max_length=255, blank=True, null=True)
    acc_type = models.IntegerField(choices=[(0, 'D'), (const.YD_ACCOUNT_TYPE, 'YD'),
                                            (const.YM_ACCOUNT_TYPE, 'YM')], default=0)
    enabled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'auctioneer_account'

    def __str__(self):
        return self.login
