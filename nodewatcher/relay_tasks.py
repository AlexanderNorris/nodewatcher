from nodewatcher import app
from models import Relay, Metric
from tcp_latency import measure_latency
import time
from cardano import Node
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


def determine_host(relay: Relay):
    if relay.ipv4:
        host = relay.ipv4
    elif relay.dns:
        host = relay.dns
    elif relay.ipv6:
        host = relay.ipv6
    return host


@app.task(name="gather_metrics")
def gather_metrics():
    """
    Gather metrics
    """
    all_relays = Relay.select()
    if len(all_relays) == 0:
        logger.info("No relays found in database yet")
    for relay in all_relays:
        host = determine_host(relay)
        port = relay.port
        tcp_latency = measure_latency(host=host, port=port)
        if tcp_latency:
            state = True
            node = Node(host, port)
            start = time.time()
            node.handshake()
            handshake_latency = time.time() - start
        else:
            handshake_latency = None
        Metric(
            tcp_state=state,
            tcp_latency=tcp_latency,
            handshake_latency=handshake_latency,
        )
    return
