import os

from pythonjsonlogger import jsonlogger


class ElasticJsonFormatter(jsonlogger.JsonFormatter):
    """
    Formatter used to log data to elastic search.
    Formats log data into *json * format.
    """
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record['index'] = 'mdev'
        log_record['cls_token'] = ''
        log_record['docker_id'] = os.environ.get('HOSTNAME', None)
        log_record['component_name'] = 'auctioneer'
        log_record['component_version'] = os.environ.get('VERSION', None)
        log_record['msg'] = log_record.pop('message', '')
        log_record['severity'] = log_record.pop('levelname', '').lower()
        log_record['response_code'] = log_record.pop('status_code', None)
        log_record.pop('server_time', None)
        log_record.pop('request', None)
        log_record.pop('asctime', None)