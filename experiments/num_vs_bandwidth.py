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
Q: Why publishing all the messages concurrently?

A: I think that describes more the relation between number of
messages and bandwidth than publishing `n` messages sequentially.
Besides being a more realistic production scenario.

Q: Why run independent experiments and aggregate their results
   instead of running one long experiment with multiple message
   batches?

A: By setting up a fresh, clean network for each set of parameters
   (e.g., for 10 messages, then for 20, etc.), we ensure that each
   run is an independent, controlled experiment. This allows us to
   isolate the impact of our single variable (number of messages)
   on bandwidth
"""

from dataclasses import dataclass
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
NUM_NODES = 20
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
POST_PUBLISH_WAIT_S = 10

# Time to wait for the pubsub mesh to form after all nodes have
# subscribed.
WAIT_AFTER_SUBSCRIPTIONS_S = 10

WAIT_CAN_SUBSCRIBE_S = 10


@dataclass
class ExperimentInfo:
    num_messages: int
    df: pd.DataFrame


def do_experiment(num_nodes: int, messages_per_node: int) -> ExperimentInfo | None:
    """
    Runs a single, isolated experiment and returns a dataframe.

    This function is a pure "data producer." It is responsible for
    the complete lifecycle of one experiment run but does not
    perform any analysis itself.
    """
    total_msgs = num_nodes * messages_per_node
    logger.info(
        f"Starting experiment: {num_nodes} nodes, "
        f"{messages_per_node} messages per node."
        f"total messages: {total_msgs}"
    )
    records: List[Dict[str, Any]] = []

    with Mesh(
        num_nodes=num_nodes, bootstrappers_num=1, image_name=WAKU_IMAGE_NAME
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
                target=poll_libp2p_bytes_metrics,
                args=(stop_event, waku_clients, records),
            )
            polling_thread.start()

            # Establish baseline traffic
            logger.info(f"Collecting baseline metrics for {BASELINE_WAIT_S}s...")
            time.sleep(BASELINE_WAIT_S)

            # Publish messages from all nodes
            logger.info(
                f"Publishing {messages_per_node} messages from each of the {num_nodes} nodes..."
            )

            # PUBLISH.1: Prepare all publishing tasks in advance.
            publish_tasks = []
            for node_id, waku_client in waku_clients.items():
                for i in range(messages_per_node):
                    msg = client.create_waku_message(
                        payload=f"msg-{i}-{node_id}",
                        content_topic=CONTENT_TOPIC,
                    )
                    publish_tasks.append((waku_client, msg))

            # PUBLISH.2. Use a thread pool to publish all messages concurrently.
            with ThreadPoolExecutor() as executor:
                # list() ensures we wait for all messages to be sent.
                list(
                    executor.map(
                        lambda task: task[0].publish_message(PS_TOPIC, task[1]),
                        publish_tasks,
                    )
                )

            logger.info("All messages published.")

            # Collect data post-publishing
            logger.info(
                f"Waiting {POST_PUBLISH_WAIT_S}s for all messages to propagate..."
            )
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
        return

    return ExperimentInfo(total_msgs, pd.DataFrame(records))


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


def plot_time_series(experiments: list[ExperimentInfo], filename: str):
    # TODO
    pass


def analyze_and_plot_aggregate(
    experiments: list[ExperimentInfo], filename: str, num_nodes: int
):
    """
    Analyzes data from multiple experiment runs and plots the
    aggregate relationship between the number of messages and
    network bandwidth cost.

    For each experiment, it calculates the "Total Net Bandwidth Cost"
    by summing the byte increase across all nodes. It then plots
    these costs against the total number of messages sent in each
    experiment
    """
    logger.info(f"Analyzing and plotting aggregate results to {filename}...")
    plot_data = []

    for experiment in experiments:
        df = experiment.df

        # It gets the increase in bytes for each node (max - min)
        # and sums them for a total network cost. This works because
        # `libp2p_network_bytes_total` is a cumulative counter
        agg_df = df.groupby("node")["total_bytes"].agg(["max", "min"])
        net_bandwidth_cost = (agg_df["max"] - agg_df["min"]).sum()

        plot_data.append(
            {
                "total_messages": experiment.num_messages,
                "net_bandwidth_cost_mb": net_bandwidth_cost / (1024 * 1024),
            }
        )

    if not plot_data:
        logger.warning("No data to plot for aggregate analysis.")
        return

    summary_df = pd.DataFrame(plot_data)

    # Create the plot
    plt.figure(figsize=(12, 8))
    sns.set_theme(style="whitegrid")

    # Using regplot to show the linear relationship and confidence interval
    plot = sns.regplot(
        x="total_messages",
        y="net_bandwidth_cost_mb",
        data=summary_df,
        ci=95,  # Show 95% confidence interval
    )

    plot.set_title(
        f"Total Messages Sent vs. Net Bandwidth Cost ({num_nodes} nodes)",
        fontsize=16,
        fontweight="bold",
    )
    plot.set_xlabel("Total Number of Messages Sent (across all nodes)", fontsize=12)
    plot.set_ylabel("Net Bandwidth Cost (MB)", fontsize=12)

    # Save the plot
    plt.savefig(filename)
    plt.close()
    logger.info(f"Aggregate plot saved to {filename}")


def main():
    # TODO: accept cmd args for num of nodes
    logger.info("Starting bandwidth measurement session.")

    messages_per_node_configs = [1, 2, 4, 8]
    all_summaries = []

    for msg_count in messages_per_node_configs:
        # 1. Run one isolated experiment to get the raw data.
        experiment = do_experiment(num_nodes=NUM_NODES, messages_per_node=msg_count)

        if experiment is None or experiment.df.empty:
            logger.warning(f"Skipping plot for {msg_count} msgs/node due to no data.")
            continue

        all_summaries.append(experiment)

    # 2. time-series for all experiments
    time_series_fs = "results/num_vs_bandwidth_timeseries.png"
    plot_time_series(all_summaries, time_series_fs)

    # 3. aggregated analysis comparing effect of different number of msgs
    aggregated_fs = "results/num_vs_bandwidth.png"
    analyze_and_plot_aggregate(all_summaries, aggregated_fs, NUM_NODES)

    logger.info("Bandwidth measurement session finished.")


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    main()
