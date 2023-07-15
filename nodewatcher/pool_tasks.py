from celery import Celery, shared_task
from celery.schedules import crontab
from models import Pool, Relay
import requests
from celery.utils.log import get_task_logger
from nodewatcher import app
from time import sleep

logger = get_task_logger(__name__)

session = requests.Session()
session.headers = {"User-Agent": "NodeWatcher Release 0.1"}
POOL_SIZE_QUERY = 100


def divide_chunks(l: list, n: int):
    """
    Limit size of requests
    """
    for i in range(0, len(l), n):
        yield l[i : i + n]


@app.task(name="update_pools")
def update_pools():
    """
    Obtain all pools
    """
    # initial query for
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
    logger.info(f"Gathered {len(all_pools)} total live pools")
    # Begin gathering all pool details and writing to database
    bechs_only = [pool["pool_id_bech32"] for pool in all_pools]
    logger.info(f"Gathering data for pools in chunks of: {POOL_SIZE_QUERY}")
    for bech in divide_chunks(bechs_only, POOL_SIZE_QUERY):
        # Optimise this to run bulk bech fetches (not all)
        # Keep memory efficient
        responses = session.post(
            "https://api.koios.rest/api/v0/pool_info",
            json={"_pool_bech32_ids": [bech]},
        ).json()
        # Slow down the sleep queries
        sleep(1)
        # Form object to push into database
        for response in responses:
            # Koios API sometimes returns a None response e.g. for WAV13
            if not response:
                continue
            try:
                ticker = response.get("meta_json", {}).get("ticker")
                logger.info(f"Writing to database {ticker}")
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
                    meta_json_name=response.get("meta_json", {}).get("name"),
                    meta_json_ticker=response.get("meta_json", {}).get("ticker"),
                    meta_json_homepage=response.get("meta_json", {}).get("homepage"),
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
                # Rate limiting sigh
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
    return all_pools
