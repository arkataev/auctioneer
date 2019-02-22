from django.conf import settings
from django.contrib import admin

from auctioneer.models import KeywordBidRule
from common.task_runner.admin import ExtendedResultDataKw, KeywordbidTaskInline


class KeyworBidAdmin(admin.ModelAdmin):
    """"""
    actions = None
    inlines = [KeywordbidTaskInline, ExtendedResultDataKw]
    list_display = ('title', 'account', 'target_bid_diff', 'bid_increase_percentage', 'max_bid')


admin.site.register(KeywordBidRule, KeyworBidAdmin)
admin.site.site_header = f"Auctioneer. The Direct Marketing Tool v.{settings.VERSION}"
