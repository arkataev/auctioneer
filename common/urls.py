from django.urls import path, include
from django.contrib import admin
from common.reporter import listeners, collectors
from common import signals
from celery.signals import task_failure, task_postrun


urlpatterns = [
    path('', admin.site.urls),
    path('account/', include('common.account.urls'))
]

# signal connection. Urls are imported once om application start
collectors.set_keyword_bids_params_transceiver.add_signals(signals.params_interceptor, task_failure)
collectors.calculate_keyword_bids_task_result_transceiver.add_signals(task_postrun)
collectors.set_keyword_bids_params_transceiver.add_observers(listeners.kwb_total_listener)
collectors.calculate_keyword_bids_task_result_transceiver.add_observers(listeners.kwb_calc_result_listener)
