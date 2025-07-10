import logging
import threading
import time
from typing import Any, Dict, List

from concurrent.futures import ThreadPoolExecutor

from nwaku import client

POLL_INTERVAL_S = 1

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


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
