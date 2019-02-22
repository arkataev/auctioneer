"""
When setting some keyword bids, user usually wants to check which of them succeeded.
This module contains implementations of application execution results collection logic.
"""

import logging

from common import signals
from . import builders


_logger = logging.getLogger(__file__)


class CalculateKeywordBidsTaskResultListener(signals.Listener):
    """
    A listener for collecting task result data.

    As celery task completes it will initiate a signal
    (more on celery signals `here <http://docs.celeryproject.org/en/latest/userguide/signals.html#task-signals>`_)
    that will be transfered to all signal listeners.
    This class is meant to be one of such listeners. Signal will contain some useful data that should be
    used to build :py:class:`auctioneer.models.KeywordBidTaskResult` model

    """

    def __init__(self, builder: builders.ExtendedTaskResultBuilder):
        """
        :param builder:         Extended task result builder instance
        :type builder:          ExtendedTaskResultBuilder
        """
        self._builder = builder

    def update(self, beacon):
        task_id, kwbid_id = beacon.get_data()
        self._builder.build_task_result(task_id, kwbid_id)
        self._builder.build_result()


kwb_calc_result_listener = CalculateKeywordBidsTaskResultListener(builders.ext_task_result_builder)


class CalculateKeywordBidsTotalSent(signals.Listener):
    """
    A listener for collecting total sended keyword bids.

    This is another type of listener, but unlike :py:class:`CalculateKeywordBidsTaskResultListener` it listens
    for data to calculate total keyword bids number sent to YD API in
    particular request and pass this data to its builder.

    """

    def __init__(self, builder: builders.ExtendedTaskResultBuilder):
        """
        :param builder:         Extended task result builder instance
        :type builder:          ExtendedTaskResultBuilder
        """
        self._builder = builder

    def update(self, beacon):
        keyword_bids = beacon.get_data()
        self._builder.build_total(len(*keyword_bids) if keyword_bids else 0)
        self._builder.build_result()


kwb_total_listener = CalculateKeywordBidsTotalSent(builders.ext_task_result_builder)
