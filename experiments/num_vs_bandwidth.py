"""
Number of messages <-> Bandwidth

This script addresses the problem of understanding how bandwidth
usage in a Waku network is affected by the number of messages
being sent. It creates a decentralized, many-to-many traffic
pattern where all nodes in the network publish messages
concurrently.

The analysis is presented through two primary visualizations:
1.  A Time-Series Plot: For each individual experiment run, this
    plot shows the bandwidth consumption over time. It
    provides a clear visual of the network's behavior.
2.  An Aggregate Comparison Plot: This final plot collates the
    results from all runs. It plots the Total Net Bandwidth
    Cost against the Total Number of Messages Sent. This key
    visualization directly illustrates the relationship between
    message load and the overall network cost.

Used NWaku metrics for the experiment: libp2p_network_bytes_total

Design Decisions:
-----------------------
Q: Why run independent experiments and aggregate their results
   instead of running one long experiment with multiple message
   batches?

A: By setting up a fresh, clean network for each set of parameters
   (e.g., for 10 messages, then for 20, etc.), we ensure that each
   run is an independent, controlled experiment. This allows us to
   isolate the impact of our single variable (number of messages)
   on bandwidth.
"""

import logging
import threading
import time
from typing import Any, Dict, List

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from concurrent.futures import ThreadPoolExecutor

from mesh.mesh import Mesh
from nwaku import client

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Experiment config
NUM_NODES = 5
WAKU_IMAGE_NAME = "wakuorg/nwaku"
PS_TOPIC = "/waku/2/default-waku/proto"
CONTENT_TOPIC = "my-content-topic"

# Timing config
POLL_INTERVAL_S = 1

# Time to wait for the network to stabilize and collect baseline
# metrics before publishing.
BASELINE_WAIT_S = 15

# Time to wait after publishing for messages to propagate and be
# reflected in metrics.
POST_PUBLISH_WAIT_S = 20

# Time to wait for the pubsub mesh to form after all nodes have
# subscribed.
WAIT_AFTER_SUBSCRIPTIONS_S = 10

WAIT_CAN_SUBSCRIBE_S = 10


def do_experiment(num_nodes: int, messages_per_node: int) -> pd.DataFrame:
    """
    Runs a single, isolated experiment and returns a dataframe.

    This function is a pure "data producer." It is responsible for
    the complete lifecycle of one experiment run but does not
    perform any analysis itself.
    """
    logger.info(
        f"Starting experiment: {num_nodes} nodes, "
        f"{messages_per_node} messages per node."
        f"total messages: {num_nodes * messages_per_node}"
    )
    records: List[Dict[str, Any]] = []

    with Mesh(
        num_nodes=num_nodes, bootstrappers_num=1, image_name=WAKU_IMAGE_NAME
    ) as mesh:
        waku_clients: Dict[str, client.WakuRestClient] = {}
        polling_thread: threading.Thread | None = None
        stop_event: threading.Event | None = None
        try:
            for node in mesh.all_nodes:
                waku_clients[node.id] = client.WakuRestClient(
                    ip_address="localhost",
                    rest_port=node.rest_port,
                    metrics_port=node.metrics_port,
                )

            logger.info("Waiting for REST API to be ready for subscriptions...")
            time.sleep(WAIT_CAN_SUBSCRIBE_S) 
            logger.info("Subscribing all nodes to the pubsub topic...")
            with ThreadPoolExecutor() as executor:
                # list to wait for evaluation of all threads
                list(
                    executor.map(
                        lambda w_client: w_client.subscribe_to_pubsub_topic([PS_TOPIC]),
                        waku_clients.values(),
                    )
                )

            logger.info("Waiting for gossipsub mesh to form...")
            time.sleep(WAIT_AFTER_SUBSCRIPTIONS_S)

            # Start background metrics polling
            stop_event = threading.Event()
            polling_thread = threading.Thread(
                target=_poll_metrics, args=(stop_event, waku_clients, records)
            )
            polling_thread.start()

            # Establish baseline traffic
            logger.info(f"Collecting baseline metrics for {BASELINE_WAIT_S}s...")
            time.sleep(BASELINE_WAIT_S)

            # Publish messages from all nodes
            logger.info(
                f"Publishing {messages_per_node} messages from each of the {num_nodes} nodes..."
            )
            for node_id, waku_client in waku_clients.items():
                # TODO: use threads to make the publishing concurrent?
                for i in range(messages_per_node):
                    msg = client.create_waku_message(
                        payload=f"msg-{i}-{node_id}",
                        content_topic=CONTENT_TOPIC,
                    )
                    waku_client.publish_message(PS_TOPIC, msg)
            logger.info("All messages published.")

            # Collect data post-publishing
            logger.info(f"Waiting {POST_PUBLISH_WAIT_S}s for messages to propagate...")
            time.sleep(POST_PUBLISH_WAIT_S)

        except Exception as e:
            logger.error(f"An error occurred during the experiment: {e}", exc_info=True)
            raise  # Re-raise the exception to terminate the failed run.

        finally:
            # Ensure polling stops and clients are closed
            if polling_thread and polling_thread.is_alive():
                logger.info("Stopping metrics polling...")
                if stop_event:
                    stop_event.set()
                polling_thread.join()

            for waku_client in waku_clients.values():
                waku_client.close()

    logger.info(f"Experiment finished. Collected {len(records)} data points.")

    if not records:
        logger.warning("No data was collected during the experiment.")
        return pd.DataFrame()

    return pd.DataFrame(records)


def _poll_metrics(
    stop_event: threading.Event,
    waku_clients: Dict[str, client.WakuRestClient],
    records: List[Dict[str, Any]],
):
    # TODO: get metrics in parallel for a more accurate representation
    # of the network at a given time
    while not stop_event.is_set():
        for node_id, waku_client in waku_clients.items():
            try:
                metrics_raw = waku_client.get_metrics()
                scraped_metrics = client.scrape_metrics(
                    metrics_raw, "libp2p_network_bytes_total"
                )
                for metric in scraped_metrics:
                    records.append(
                        {
                            "timestamp": time.time(),
                            "node": node_id,
                            "direction": metric["labels"]["direction"],
                            "total_bytes": metric["value"],
                        }
                    )
            except Exception as e:
                logger.error(f"Error polling metrics for {node_id}: {e}")

        if stop_event.wait(POLL_INTERVAL_S):
            break


def plot_time_series(raw_data: pd.DataFrame, filename: str):
    # TODO
    pass


def analyze_and_plot_aggregate(results: list[dict]):
    pass


def main():
    # TODO: accept cmd args for num of nodes
    logger.info("Starting bandwidth measurement session.")

    messages_per_node_configs = [2]
    all_summaries = []

    for msg_count in messages_per_node_configs:
        # 1. Run one isolated experiment to get the raw data.
        raw_data_df = do_experiment(num_nodes=NUM_NODES, messages_per_node=msg_count)

        if raw_data_df.empty:
            logger.warning(f"Skipping plot for {msg_count} msgs/node due to no data.")
            continue

        total_msg_count = msg_count * NUM_NODES
        # 2. Generate the diagnostic time-series plot for this run.
        run_name = f"{NUM_NODES}nodes_{total_msg_count}msgs"
        plot_time_series(raw_data_df, f"testdata/timeseries_{run_name}.png")

        all_summaries.append(
            {
                "msg_count": total_msg_count,
                "raw_data": raw_data_df,
            }
        )

    # 4. Analyze all collected summaries and make the final plot.
    analyze_and_plot_aggregate(all_summaries)

    logger.info("Bandwidth measurement session finished.")


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    main()
