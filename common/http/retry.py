import time
from logging import getLogger
from types import GeneratorType
from .exceptions import MaxRetry


_logger = getLogger(__name__)


class gateway_retry:

    def __init__(self, retry_codes, max_retries=3, backoff=0.1):
        self.retry_codes = retry_codes
        self._max_retries = max_retries
        self._backoff = backoff
        self._retry_count = 0

    @property
    def backoff(self):
        self._backoff = self._backoff * (pow(self._max_retries - 1, 2))
        return self._backoff

    @property
    def can_retry(self):
        return self._retry_count <= self._max_retries

    def reset_retry(self):
        self._retry_count = 0
        self._backoff = 0.1

    def __enter__(self):
        self._retry_count += 1
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.reset_retry()

    def __call__(self, generator):
        def wrapper(*args, **kwargs) -> GeneratorType:
            for result in generator(*args, **kwargs):
                if 'error_code' in result and result['error_code'] in self.retry_codes:
                    # Gateway expectes to receive particular data on status-200 response. But in some cases Yandex API
                    # may return unexpected data. Typically those are status-200 responses,
                    # but has errors inside response-body (because service was unable to process request)
                    with self:
                        if self.can_retry:
                            _logger.debug(f'Retry count: {self._retry_count}. '
                                          f'Backoff: {self._backoff}. Reason: {result}')
                            time.sleep(self.backoff)
                            yield from wrapper(*args, **kwargs)
                        else:
                            raise MaxRetry(f'Max retries exceeded with error {result}')
                else:
                    yield result
        return wrapper