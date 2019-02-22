"""
Here we implement type that will be responsible for reports and task results creation.
Each report builder may be used to create custom types of reports and implement some report logic, like
formatting (csv, xlsx, sql etc.).
"""
import json
import logging

from django.core.exceptions import ValidationError
from django_celery_results.models import TaskResult
from auctioneer.controllers.keyword_bid_rule import get_keywordbid_rule
from common.task_runner.models import KeywordBidTaskResult

_logger = logging.getLogger(__name__)


class ExtendedTaskResultBuilder:
    """
    Gathers data and builds gradually :py:class:`KeywordBidTaskResult` model as data received.
    This is an implementation of `Builder <https://refactoring.guru/design-patterns/builder>`_
    pattern that allows creating objects in a number of steps gathering necessary data on each step.
    When all data gathered the object can be built.::

        builer = ExtendedTaskResultBuilder()
        builder.build_total(10)
        builder.build_task_result(task_id, kwb_rule_id)
        builder.buld_result()       # this will actually create and save model in DB

    """
    def __init__(self):
        self.result: KeywordBidTaskResult = None
        self._model = KeywordBidTaskResult()

    def build_result(self):
        """
        This implementation of Builder does not return actual result, but saves a django model to DB
        when all model fields are *cleaned* (properly set).

        :rtype:  None
        """
        try:
            # full_clean checks if all model attributes are properly set and raises ValidationError if they're not
            self._model.full_clean()
        except ValidationError:
            pass
        else:
            # when all model fields set, Builder can save the model
            self._model.save()
            self.result = self._model
            _logger.debug(f'Created {self._model.__class__.__name__}: {self._model.id}')
            self.reset()

    def reset(self):
        self._model = KeywordBidTaskResult()

    def build_total(self, total: int):
        """
        Sets :py:attr:`auctioneer.models.KeywordBidTaskResult.total` attribute

        :param total:       KeywordBidTaskResult total keywordbids sent
        :type total:        int
        :rtype:             None
        """
        _logger.debug(f'Recieved total keyword_bids sent {total}')
        self._model.total = total

    def build_task_result(self, task_id: int, kw_bid_rule_id: int):
        """
        Sets :py:class:`auctioneer.models.KeywordBidTaskResult` attributes.

        This method will actually fill all the rest fields in the model.

        :param task_id:        celery task id
        :param kw_bid_rule_id: keyword_bid rule id
        :type task_id:         int
        :type kw_bid_rule_id:  int
        :rtype:                None
        """
        task_result, task_data = self._get_task_data(task_id)
        keyword_bid_rule = get_keywordbid_rule(kw_bid_rule_id)
        warnings, errors, success = self._parse_keyword_bids_set_result(task_data)
        is_ok = all([not warnings, not errors, task_result.status == 'SUCCESS', success])
        result = {'celery_task': task_result,
                  'errors': errors,
                  'warnings': warnings,
                  'success': success,
                  'kw_bid_rule': keyword_bid_rule,
                  'is_ok': is_ok,
                  'extra_data': {}
                  }
        _logger.debug(f'Recieved task results {result}')
        for k, v in result.items():
            setattr(self._model, k, v)

    @staticmethod
    def _get_task_data(task_id) -> (TaskResult, {}):
        try:
            task_result = TaskResult.objects.get(task_id=task_id)
        except TaskResult.DoesNotExist:
            _logger.debug(f'TaskResult for task_id {task_id} does not exist')
            data = {}
            task_result = None
        else:
            data = json.loads(task_result.result)
        return task_result, data

    @staticmethod
    def _parse_keyword_bids_set_result(data: dict) -> tuple:
        """
        Parse keyword bids *set* response body.

        A *set* response from YD API contains information of which items in *set* request where processed
        with warnings, error or success. Here we extract this data from response body and count how many warnings,
        errors or success does response have. This mainly used to provide some info to user on requests results
        in admin interface.

        :param data:            YD keyword bids *set* reponse data
        :type data:             dict
        :rtype:                 tuple
        :return:                number of warnings, errors and success in response; (warnings, errors, success)
        """
        warnings = errors = 0
        for r in data:
            warnings += len(r.pop('Warnings', []))
            errors += len(r.pop('Errors', []))
        success = len(data) - warnings - errors
        _logger.debug(f'Calculate_keyword_bids_results: Warnings: {warnings}, Errors: {errors}, Success: {success}')
        return warnings, errors, success


ext_task_result_builder = ExtendedTaskResultBuilder()
