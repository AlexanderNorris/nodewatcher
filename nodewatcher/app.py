from flask import Flask
from typing import Dict, List, Generator
import logging
import requests

logging.basicConfig(level=logging.INFO)
LIVE_POOL_QUERY = 1000
POOL_DETAIL_SIZE_QUERY = 100

app = Flask(__name__)


@app.route("/")
def get_targets():
    result = get_all_targets()
    return result


def divide_chunks(l: List[Dict], n: int) -> Generator[List[Dict], None, None]:
    """
    Limit size of requests
    """
    for i in range(0, len(l), n):
        yield l[i : i + n]


def determine_host(relay):
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


def get_all_pools(session: requests.Session) -> List[Dict]:
    """
    Fetch all active stake pools
    """
    all_pools = []
    pagination_incomplete = True
    offset = 0
    session = requests.Session()
    session.headers = {"User-Agent": "NodeWatcher Release 0.2"}
    while pagination_incomplete:
        response = session.get(
            "https://api.koios.rest/api/v1/pool_list",
            params={
                "offset": str(offset),
                "pool_status": "eq.registered",
                "order": "pool_id_bech32.desc",
            },
        ).json()
        all_pools += response
        logging.debug(f"Length of the response: {len(response)}")
        if len(response) < LIVE_POOL_QUERY:
            pagination_incomplete = False
        offset += LIVE_POOL_QUERY
    logging.info(f"All pools count: {len(all_pools)}")
    return all_pools


def get_pool_data(session, bech_group: list):
    try:
        response = session.post(
            "https://api.koios.rest/api/v1/pool_info",
            json={"_pool_bech32_ids": bech_group},
        )
        logging.info(response.status_code)
        thing = response.json()
        return thing
    except Exception as e:
        # print(e)
        logging.exception(e)
    return []


def get_all_targets():
    """
    Obtain all pools
    """
    results = []
    targets = []
    session = requests.Session()
    session.headers = {"User-Agent": "NodeWatcher Release 0.2"}
    all_pools = get_all_pools(session)
    # Begin gathering all pool details
    bechs_only = [pool["pool_id_bech32"] for pool in all_pools]
    logging.info(f"Gathered {len(all_pools)} total live pools")

    for bech_group in divide_chunks(bechs_only, POOL_DETAIL_SIZE_QUERY):
        logging.info(f"Fetching pool data for {len(bech_group)} pools")
        # Optimise this to run bulk bech fetches (not all)
        # Keep memory efficient
        results.extend(get_pool_data(session, bech_group))
    count = 0
    for result in results:
        relay_list = []
        meta_json = result.get("meta_json", {})
        if not meta_json:
            pool_ref = "Invalid Metadata"
        else:
            pool_ref = result.get("meta_json", {}).get("ticker", "Invalid Metadata")
        pool_bech = result.get("pool_id_bech32", "No bech!?!?")
        relays = result.get("relays", [])
        for relay in relays:
            relay_address = determine_host(relay)
            relay_port = relay["port"]
            relay_list.append(f"{relay_address}:{relay_port}")
            targets.append(
                {
                    "targets": relay_list,
                    "labels": {"ticker": pool_ref, "bech": pool_bech},
                }
            )
    logging.info(f"Problems with a total of: {count} pools")
    return targets
