from common.reporter.builders import ExtendedTaskResultBuilder


def test_parse_keyword_bids_set_result(keyword_bids_w_warnings):
    data = keyword_bids_w_warnings['result']['SetResults']
    warnings, errors, success = ExtendedTaskResultBuilder._parse_keyword_bids_set_result(data)
    assert warnings == 6
    assert errors == 6
    assert success == 1502


def test_build_result(task_result, kwb_rule):
    builder = ExtendedTaskResultBuilder()
    builder.build_task_result(task_result.id, kwb_rule.id)
    builder.build_total(10)
    builder.build_result()
    result = builder.result
    assert not result.is_ok
    assert result.warnings == 6
    assert result.errors == 6
    assert result.success == 1502
    assert result.celery_task.id is task_result.id
    assert result.kw_bid_rule == kwb_rule
    assert result.total == 10
