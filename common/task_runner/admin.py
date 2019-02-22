from django.contrib import admin
from django.forms.models import BaseInlineFormSet
from django.utils.html import mark_safe

from .models import KeywordBidTaskResult, KeywordBidTask


class KeywordbidTaskInline(admin.TabularInline):
    """"""
    model = KeywordBidTask
    fields = ['target', 'interval', 'crontab', 'expires', 'one_off', 'enabled']
    extra = 0
    max_num = 1

class LimitedResultsFs(BaseInlineFormSet):
    """Limits amount of TaskResult items to _limit and orders by date_done DESC"""
    _limit = 5

    def get_queryset(self):
        qs = super().get_queryset().order_by('-celery_task__date_done')
        return qs[:self._limit]


class ExtendedResultData(admin.TabularInline):
    """"""
    can_delete = False
    model = KeywordBidTaskResult
    extra = 0
    exclude = ('kw_bid_rule',)
    fk_name = 'celery_task'
    readonly_fields = ('rule_link', 'account', 'extra_data', 'success', 'errors', 'warnings', 'total', 'is_ok')

    def account(self, obj):
        return mark_safe(f"<a href=/auctioneer/account/{obj.kw_bid_rule.account.id}>{obj.kw_bid_rule.account.login}</a>")

    def has_add_permission(self, request, obj):
        return False

    def rule_link(self, obj):
        return mark_safe(f"<a href=/auctioneer/keywordbidrule/{obj.kw_bid_rule.id}>{obj.kw_bid_rule.title}</a>")


class ExtendedResultDataKw(ExtendedResultData):
    """"""
    fk_name = 'kw_bid_rule'
    list_display = ('status', )
    exclude = ['celery_task', 'extra_data',]
    readonly_fields = ('task_link', 'date_done', 'success', 'errors', 'warnings', 'total', 'is_ok')
    formset = LimitedResultsFs
    model = KeywordBidTaskResult

    def task_link(self, obj):
        return mark_safe(
            f"<a href=/django_celery_results/taskresult/{obj.celery_task_id}>{obj.celery_task.task_id}</a>")

    def date_done(self, obj):
        date = obj.celery_task.date_done
        return date
