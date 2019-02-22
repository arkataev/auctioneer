"""
Collection of data collectors objects. Basic data collectors implemented as Transceivers - they receive some
data from other parts of application as Signals then pass unprocessed data to all its listeners, which in turn
may process it as needed.
"""

from common import signals, http
from common.task_runner.tasks import calculate_keyword_bids


class CalculateKeywordBids(signals.Transceiver):
    """
    This beacon emits processed data, recieved from celery task.

    This is a targeted tranceiver, meaning it will receive signals only from one type of sender:
    calculate_keyword_bids() task in this case. Client code should use its instances to receive calculate_keyword_bids
    task signals.

    """
    target_sender = calculate_keyword_bids

    def process_signal(self, sender, *args, **kwargs):
        task_id = kwargs.get('task_id')
        kw_bid_rule_id, *_ = kwargs.get('args')
        self._data = (task_id, kw_bid_rule_id)
        self.notify()


calculate_keyword_bids_task_result_transceiver = CalculateKeywordBids()


class SetKeywordBidsParamsTransceiver(signals.Transceiver):
    """
    This is a :py:class:`auctioneer.signals.Transceiver` type that should
    recieve data from :py:class:`auctioneer.signals.ParamsInterceptorSignal` and pass it to connected
    listeners.

    Particularly this type should collect data from :py:meth:`YandexDirectGateway.set_keyword_bids`
    """
    target_sender = http.YandexDirectGateway.set_keyword_bids.__name__

    def process_signal(self, sender, *args, **kwargs):
        # if task has failed before keyword_bids was sent we need to set
        # total value manually to construct KeywordBidTaskResult
        self._data = kwargs.get('args') if 'exception' not in kwargs else None
        self.notify()


set_keyword_bids_params_transceiver = SetKeywordBidsParamsTransceiver()
