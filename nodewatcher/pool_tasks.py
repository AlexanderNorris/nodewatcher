from models import Pool, Relay
import requests
from celery.utils.log import get_task_logger
from nodewatcher import app
from time import sleep
from typing import Dict, List, Generator
from celery import signals

logger = get_task_logger(__name__)

session = requests.Session()
session.headers = {"User-Agent": "NodeWatcher Release 0.1"}
POOL_SIZE_QUERY = 1000


def divide_chunks(l: List[Dict], n: int) -> Generator[List[Dict], None, None]:
    """
    Limit size of requests
    """
    for i in range(0, len(l), n):
        yield l[i : i + n]


def write_pool(response: Dict):
    """
    Write to database
    """

    if response.get("meta_json"):
        ticker = response.get("meta_json", {}).get("ticker")
        name = response.get("meta_json", {}).get("name")
        homepage = response.get("meta_json", {}).get("homepage")
        logger.info(f"Writing to database {ticker}")
    else:
        bech_32 = response.get("pool_id_bech32")
        ticker = None
        name = None
        homepage = None
        logger.info(f"Writing to database for pool, no ticker {bech_32}")
    try:
        pool = Pool.get_or_create(
            pool_id_bech32=response.get("pool_id_bech32"),
            pool_id_hex=response.get("pool_id_hex"),
            active_epoch_no=response.get("active_epoch_no"),
            vrf_key_hash=response.get("vrf_key_hash"),
            margin=response.get("margin"),
            fixed_cost=response.get("fixed_cost"),
            pledge=response.get("pledge"),
            reward_addr=response.get("reward_addr"),
            # meta_url=response.get("owners"),  # This will be a relationship
            # meta_hash=response.get("relays"), # This will be a relationship
            meta_json_name=name,
            meta_json_ticker=ticker,
            meta_json_homepage=homepage,
            pool_status=response.get("pool_status"),
            retiring_epoch=response.get("retiring_epoch"),
            op_cert=response.get("op_cert"),
            op_cert_counter=response.get("op_cert_counter"),
            active_stake=response.get("active_stake"),
            sigma=response.get("sigma"),
            block_count=response.get("block_count"),
            live_pledge=response.get("live_pledge"),
            live_stake=response.get("live_stake"),
            live_delegators=response.get("live_delegators"),
            live_saturation=response.get("live_saturation"),
        )
        if isinstance(pool, tuple):
            pool = pool[0]
        for relay in response.get("relays", []):
            Relay.get_or_create(
                dns=relay.get("dns"),
                srv=relay.get("srv"),
                ipv4=relay.get("ipv4"),
                ipv6=relay.get("ipv6"),
                port=relay.get("port"),
                pool_id=pool.id,
            )
    except Exception as e:
        logger.exception(e)
    return


def get_all_pools() -> List[Dict]:
    """
    Fetch all stake pools
    """
    all_pools = []
    pagination_incomplete = True
    offset = 0
    while pagination_incomplete:
        response = session.get(
            "https://api.koios.rest/api/v0/pool_list", params={"offset": str(offset)}
        ).json()
        all_pools += response
        logger.debug(f"Length of the response: {len(response)}")
        if len(response) < 1000:
            pagination_incomplete = False
        offset += 1000
        logger.debug(f"New offset: {offset}")
    return all_pools


@app.task(name="update_pools")
def update_pools():
    """
    Obtain all pools
    """
    all_pools = get_all_pools()
    logger.info(f"Gathered {len(all_pools)} total live pools")
    # Begin gathering all pool details and writing to database
    bechs_only = [pool["pool_id_bech32"] for pool in all_pools]
    logger.info(f"Gathering data for pools in chunks of: {POOL_SIZE_QUERY}")
    for bech_group in divide_chunks(bechs_only, POOL_SIZE_QUERY):
        # Optimise this to run bulk bech fetches (not all)
        # Keep memory efficient
        responses = session.post(
            "https://api.koios.rest/api/v0/pool_info",
            json={"_pool_bech32_ids": [bech_group]},
        ).json()
        # Slow down the HTTP queries to Koios
        sleep(0.1)
        # Form object to push into database
        for response in responses:
            write_pool(response)
    return all_pools


@signals.celeryd_init.connect(sender="nodewatcher-worker1-1")
def initiate_pools(**kwargs):
    logger.info(
        "Worker ready, sleeping 60 seconds to allow database to come up prior to initial population"
    )
    sleep(60)
    update_pools()
    return
