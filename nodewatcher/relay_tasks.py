from nodewatcher import app
from models import Relay, Metric
from tcp_latency import measure_latency
import time
from cardano import Node
import pymysql.cursors
import pymysql
import datetime


def determine_host(relay: Relay):
    """
    We only need to use one of these
    """
    host = None
    if relay.get("ipv4"):
        host = relay.get("ipv4")
    elif relay.get("dns"):
        host = relay.get("dns")
    elif relay.get("ipv6"):
        host = relay.get("ipv6")
    return host


@app.task(name="measure")
def measure(host: str, port: int, relay_id: int, pool_id: int):
    """
    Determine metrics and write to database
    """
    print(f"Starting measure task for {relay_id}: {host}:{port}")
    tcp_latency = measure_latency(host=host, port=port)
    if tcp_latency:
        # TCP port open
        state = True
        try:
            node = Node(host, port)
            start = time.time()
            node.handshake()
            handshake_latency = time.time() - start
        except:
            handshake_latency = None
        tcp_latency_val = tcp_latency[0]
    else:
        # TCP port closed
        state = False
        tcp_latency_val = None
        handshake_latency = None
    print(f"Writing metric to database for {host}")
    connection = pymysql.connect(
        host="stats_db",
        user="stats",
        password="password",
        database="stats",
        cursorclass=pymysql.cursors.DictCursor,
    )
    with connection:
        with connection.cursor() as cursor:
            # Create a new record
            sql = "INSERT INTO `metric` (`tcp_state`, `tcp_latency`, `handshake_latency`, `relay_id`, `pool_id`, `clock`) VALUES (%s, %s, %s, %s, %s, %s)"
            cursor.execute(
                sql,
                (
                    state,
                    tcp_latency_val,
                    handshake_latency,
                    relay_id,
                    pool_id,
                    datetime.datetime.strftime(
                        datetime.datetime.now(), "%Y-%m-%d %H:%M:%S"
                    ),
                ),
            )
        connection.commit()
    return


@app.task(name="gather_metrics")
def gather_metrics():
    """
    Gather metrics
    """
    print("Running gather_metrics")
    try:
        connection = pymysql.connect(
            host="stats_db",
            user="stats",
            password="password",
            database="stats",
            cursorclass=pymysql.cursors.DictCursor,
        )

        with connection:
            with connection.cursor() as cursor:
                # Create a new record
                sql = "SELECT dns, srv, ipv4, port, id, pool_id FROM relay"
                cursor.execute(sql)
                all_relays = cursor.fetchall()
        print("Gathered all relays from local cache")
    except Exception as e:
        print(e)
    if len(all_relays) == 0:
        print("No relays found in database yet")
    for relay in all_relays:
        host = determine_host(relay)
        if not host:
            print("Could not determine host")
            continue
        port = relay.get("port")
        relay_id = relay.get("id")
        pool_id = relay.get("pool_id")
        measure.apply_async(
            kwargs={
                "host": host,
                "port": port,
                "relay_id": relay_id,
                "pool_id": pool_id,
            }
        )
        print("Completed gather metrics task!")
    return
