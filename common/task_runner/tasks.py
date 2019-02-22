"""
A collection of main application tasks and other related objects.
"""
import logging

from celery import Task
from django.conf import settings
from requests.exceptions import ConnectionError, ReadTimeout, ConnectTimeout

from auctioneer.main import run
from common import settings, celery

_logger = logging.getLogger(__file__)


@celery.app.task(name='calculate_keyword_bids', bind=True)
def calculate_keyword_bids(self, kw_bid_rule_id: int):
    """
    Celery task for calculating and setting yandex direct keywords bids

    :param self:                    task instance
    :param kw_bid_rule_id:          DB id of :py:class:`auctioneer.models.KeywordBidRule`
    :type kw_bid_rule_id:           int
    :type self:                     Task
    """
    try:
        result = run(kw_bid_rule_id)
    except (ConnectionError, ReadTimeout, ConnectTimeout) as e:
        _logger.error(f'Task error: {e}. Retrying...', exc_info=True)
        self.retry(exc=e, max_retries=settings.TASK_DEFAULT_RETRIES)
    else:
        return result
