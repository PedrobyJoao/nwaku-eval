import logging
import threading
import time
from typing import Any, Callable, Dict, List

import pandas as pd
from concurrent.futures import ThreadPoolExecutor

from mesh.mesh import Mesh
from nwaku import client

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Time constants for experiment phases
# TODO: make them proportionaly to the num of nodes
BASELINE_WAIT_S = 15
POST_ACTION_WAIT_S = 10
WAIT_AFTER_SUBSCRIPTIONS_S = 10
WAIT_FOR_API_S = 10

# Shared configuration
WAKU_IMAGE_NAME = "wakuorg/nwaku"
PUBSUB_TOPIC = "/waku/2/default-waku/proto"

POLL_INTERVAL_S = 1


def run_experiment_lifecycle(
    num_nodes: int,
    bootstrappers_num: int,
    execute_publish_scenario: Callable[[Dict[str, client.WakuClient]], None],
) -> pd.DataFrame:
    """
    Handles the generic lifecycle of a Waku network experiment.

    This function takes care of all the boilerplate: setting up the
    mesh, creating clients, subscribing nodes, running metrics polling,
    and tearing down resources.

    The `publish_action` is responsible for actually performing the
    desired experiment scenario (e.g.: publishing `n` msgs,
    publishing msgs of `s` size...)
    """
    records: List[Dict[str, Any]] = []

    with Mesh(
        num_nodes=num_nodes,
        bootstrappers_num=bootstrappers_num,
        image_name=WAKU_IMAGE_NAME,
    ) as mesh:
        waku_clients: Dict[str, client.WakuClient] = {}
        polling_thread: threading.Thread | None = None
        stop_event: threading.Event | None = None
        try:
            for node in mesh.all_nodes:
                waku_clients[node.id] = client.WakuClient(
                    ip_address="localhost",
                    rest_port=node.rest_port,
                    metrics_port=node.metrics_port,
                )

            logger.info("Waiting for REST API to be ready...")
            time.sleep(WAIT_FOR_API_S)

            logger.info("Subscribing all nodes to the pubsub topic...")
            with ThreadPoolExecutor() as executor:
                list(
                    executor.map(
                        lambda c: c.subscribe_to_pubsub_topic([PUBSUB_TOPIC]),
                        waku_clients.values(),
                    )
                )

            logger.info("Waiting for gossipsub mesh to form...")
            time.sleep(WAIT_AFTER_SUBSCRIPTIONS_S)

            stop_event = threading.Event()
            polling_thread = threading.Thread(
                target=poll_libp2p_bytes_metrics,
                args=(stop_event, waku_clients, records),
            )
            polling_thread.start()

            logger.info(f"Collecting baseline metrics for {BASELINE_WAIT_S}s...")
            time.sleep(BASELINE_WAIT_S)

            # Execute the specific experiment scenario
            execute_publish_scenario(waku_clients)

            logger.info(f"Waiting {POST_ACTION_WAIT_S}s for messages to propagate...")
            time.sleep(POST_ACTION_WAIT_S)

        except Exception as e:
            logger.error(f"An error occurred during experiment: {e}", exc_info=True)
            raise

        finally:
            if polling_thread and polling_thread.is_alive():
                logger.info("Stopping metrics polling...")
                if stop_event:
                    stop_event.set()
                polling_thread.join()

            for waku_client in waku_clients.values():
                waku_client.close()

    logger.info(f"Experiment run finished. Collected {len(records)} data points.")

    if not records:
        return pd.DataFrame()

    return pd.DataFrame(records)


def poll_libp2p_bytes_metrics(
    stop_event: threading.Event,
    waku_clients: Dict[str, client.WakuClient],
    records: List[Dict[str, Any]],
):
    """
    Polls Waku node metrics concurrently and appends them to a shared list.

    This function runs in a background thread. In a loop, it uses a
    ThreadPoolExecutor to fetch metrics from all nodes at the same time.
    This provides a more accurate snapshot of the network's state at
    each polling interval.
    """

    def _poll_single_node(node_info: tuple[str, client.WakuClient]) -> list:
        node_id, waku_client = node_info
        node_records = []
        try:
            metrics_raw = waku_client.get_metrics()
            scraped_metrics = client.scrape_metrics(
                metrics_raw, "libp2p_network_bytes_total"
            )
            for metric in scraped_metrics:
                node_records.append(
                    {
                        "timestamp": time.time(),
                        "node": node_id,
                        "direction": metric["labels"]["direction"],
                        "total_bytes": metric["value"],
                    }
                )
        except Exception as e:
            logger.error(f"Error polling metrics for {node_id}: {e}")
        return node_records

    while not stop_event.is_set():
        with ThreadPoolExecutor() as executor:
            # Map the polling function over all clients
            results_iterator = executor.map(_poll_single_node, waku_clients.items())

            # Collect results and extend the main records list
            for node_records_list in results_iterator:
                if node_records_list:
                    records.extend(node_records_list)

        # Wait for the next polling interval, or break if stopped
        if stop_event.wait(POLL_INTERVAL_S):
            break
