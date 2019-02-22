import json

from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils.crypto import get_random_string
from django_celery_beat.models import PeriodicTask, PeriodicTasks
from django_celery_results.models import TaskResult

from auctioneer.models import KeywordBidRule
from common.account.models import Account
from . import tasks



class KeywordBidTask(PeriodicTask):
    """
    Periodic task for executing keywordbid rules
    This is a
    `multitable-inheritance <https://docs.djangoproject.com/en/2.1/topics/db/models/#multi-table-inheritance>`_ ,
    meaning that every row in periodic_task table will be related to particular row in keyword_bid_task table.
    This allows to manage periodic tasks inderectly. User is provided with more simplified and customized
    KeywordBidTasks model which in turn manages PeriodicTask: If user creates new KeywordBidTask, new related
    PeriodicTask created, if KeywordBidTask deleted, related PeriodicTask is deleted too.
    In the same time this related objects would have different titles and some other attributes.
    """
    target = models.ForeignKey(KeywordBidRule, on_delete=models.CASCADE, null=True)
    """To which KeywaordBid rule this task realates"""
    task_handler_name = tasks.calculate_keyword_bids.__name__
    """
    A name of Celery task that will be executed.
    We don't want user to manually set task name as they don't know about them.
    So, the reasonable decision was to set it as some constant used around the application.
    """

    class Meta:
        verbose_name = 'Keyword bids task'
        verbose_name_plural = "Keyword bids tasks"
        db_table = 'auctioneer_keywordbidtask'

    def save(self, *args, **kwargs):
        """
        We should override a bit model save process to manage PeriodicTasks.
        This is where periodic task name, handler and params are set.
        """
        #  This is the name of periodic task in django_celery_beat_periodictask table.
        #  Name should be unique. But to be more user-friendly we ask user to only provide Rule title to which
        #  periodic task is applied. Then we use rule title to generate task name.
        self.name = f'{self.target.title}_task_{get_random_string()}'
        self.task = self.task_handler_name
        self.args = json.dumps([self.target.id])
        super(PeriodicTask, self).save(*args, **kwargs)

    def __str__(self):
        return self.name


class KeywordBidTaskResult(models.Model):
    """
    This an extended representaion of celery task execution results. Overriding and customizng default
    TaskResult model could ran tricky, so here we just create separate model and relate it to particular task result.
    """

    kw_bid_rule = models.ForeignKey(KeywordBidRule, on_delete=models.SET_NULL, null=True)
    """Link to keyword bid rule model that was used in the request"""
    celery_task = models.ForeignKey(TaskResult, on_delete=models.CASCADE, related_name='extended_result')
    """Link to Celery task that was running the request"""
    success = models.IntegerField(null=True)
    """Number of succeeded keywordbids set returned by YD API"""
    errors = models.IntegerField(null=True)
    """Number of errors returned by YD API"""
    warnings = models.IntegerField(null=True)
    """Number of warnings returned by YD API"""
    total = models.IntegerField()
    """How many keywordbids were sent to YD API"""
    is_ok = models.BooleanField()
    """Task result overall status: no errors and warnings and have success means is_ok"""
    extra_data = JSONField(blank=True)
    """Optional extra data to pass around"""

    class Meta:
        db_table = 'auctioneer_extendedtaskresult'


# On every KeywordBidTask change PeriodicTask will also be changed
models.signals.pre_delete.connect(PeriodicTasks.changed, sender=KeywordBidTask)
models.signals.pre_save.connect(PeriodicTasks.changed, sender=KeywordBidTask)
