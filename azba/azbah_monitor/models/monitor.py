import time

from odoo.http import Response
import os

from odoo.service.server import PreforkServer, memory_info
from odoo.http import JsonRequest
from odoo import http
from odoo import tools

import logging
import socket

try:
    import psutil
except ImportError:
    psutil = None

_logger = logging.getLogger(__name__)

registry = None

try:
    from prometheus_client import Counter, Gauge, CollectorRegistry, \
Summary, generate_latest, CONTENT_TYPE_LATEST, REGISTRY, Histogram
    from prometheus_client import multiprocess
except ImportError:
    _logger.error("Couldn't import Prometheus Python Client. "
                  "Make sure it's installed.")

try:
    common_labels = ['hostname', 'dbname']
    LONGPOLL_COUNTER = Counter(
        "odoo_longpolling_counter",
        "Odoo longpolling counter",
        common_labels,
    )
    RPC_RESPONSE_TIME = Histogram(
        "odoo_rpc_request_time_seconds",
        "Odoo RPC request time in seconds",
        common_labels + ['path'],
    )
    RPC_MEMORY_USAGE_DELTA = Summary(
        "odoo_rpc_memory_usage_delta_kb",
        "Odoo RPC request memory usage delta in kilobytes",
        common_labels + ['pid'],
    )
    RPC_MEMORY_USAGE = Summary(
        "odoo_rpc_memory_usage_kb",
        "Odoo RPC request memory usage after dispatch in kilobytes",
        common_labels + ['pid'],
    )

    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry)

    _logger.info('Prometheus instrumentation enabled.')

    # Monkey patch the worker exit methods. This is needed for Prometheus
    # multiprocessing mode.
    def pop_wrapper(worker_pop):
        def prometheus_worker_pop(self, pid):
            multiprocess.mark_process_dead(pid)
            worker_pop(self, pid)
            _logger.debug('Worker {} removed from Prometheus multiprocess '
                          'collector'.format(pid))
        return prometheus_worker_pop

    def kill_wrapper(worker_kill):
        def prometheus_worker_kill(self, pid, sig):
            multiprocess.mark_process_dead(pid)
            worker_kill(self, pid, sig)
            _logger.debug('Worker {} removed from Prometheus multiprocess '
                          'collector'.format(pid))
        return prometheus_worker_kill

    PreforkServer.worker_pop = pop_wrapper(PreforkServer.worker_pop)
    PreforkServer.worker_kill = kill_wrapper(PreforkServer.worker_kill)

    # Monkey patch Json RPC dispatcher to monitor RPC response
    # times and memory usage.
    def dispatch_rpc_wrapper_json(dispatch_rpc):

        def prometheus_dispatch_rpc_json(self):
            longpoll = 'longpolling' in self.httprequest.full_path
            details = dict(
                hostname=socket.gethostname(),
                dbname=self.db,
            )

            mem_details = dict(**details, pid=os.getpid())
            time_details = dict(**details, path=self.httprequest.full_path)

            start_time = time.perf_counter()
            start_memory = 0
            end_memory = 0
            if psutil:
                start_memory = memory_info(psutil.Process(os.getpid()))

            result = dispatch_rpc(self)

            if not longpoll:
                if psutil:
                    end_memory = memory_info(psutil.Process(os.getpid()))
                RPC_MEMORY_USAGE_DELTA.labels(**mem_details)\
                    .observe((end_memory - start_memory) / 1024)  # kB

                RPC_MEMORY_USAGE.labels(**mem_details)\
                    .observe(end_memory)
                duration = max(time.perf_counter() - start_time, 0)
                RPC_RESPONSE_TIME.labels(**time_details).observe(duration)
            else:
                LONGPOLL_COUNTER.labels(**details).inc()

            return result
        return prometheus_dispatch_rpc_json

    JsonRequest.dispatch = dispatch_rpc_wrapper_json(JsonRequest.dispatch)

except Exception as e:
    _logger.error('Failed to load Prometheus instrumentation. {}'
                  .format(e))


class PrometheusController(http.Controller):

    @http.route(['/metrics'], auth='none', method=['GET'])
    def metrics(self, **get):
        """
        Provide Prometheus metrics
        """

        if registry is not None:
            registry.collect()
            data = generate_latest(registry)
        else:
            data = b''

        session = http.request.session
        # We set a custom expiration of 1 second for this request, as we do a
        # lot of health checks, we don't want those anonymous sessions to be
        # kept.
        if not session.uid:
            # Will change session.should_save to False. It cannot be directly
            # accessed so we do it like this.
            session.modified = False
            session.expiration = 1

        return Response(
            data,
            mimetype=CONTENT_TYPE_LATEST
        )