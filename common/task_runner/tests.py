from common.task_runner.tasks import calculate_keyword_bids
from common import http
import pytest


@pytest.mark.celery
@pytest.mark.django_db
@pytest.mark.usefixtures('keywordbid_get_set_ok')
def test_calculate_keyword_bids(keyword_bid_rule_fixture):
    result = calculate_keyword_bids.apply((keyword_bid_rule_fixture.id,)).result
    result = result.get('SetResults')
    assert len(result) == 2  # kw_bid field name and SearchBid should be in result
    assert set(result) & set(http.constants.YD_KEYWORD_BIDS_FIELDNAMES)
