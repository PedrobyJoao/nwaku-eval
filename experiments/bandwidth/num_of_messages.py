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
from typing import Dict

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from concurrent.futures import ThreadPoolExecutor

from nwaku import client
from common import run_experiment_lifecycle, PUBSUB_TOPIC

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Experiment config
NUM_NODES = 20
CONTENT_TOPIC = "num-vs-bw-content-topic"


@dataclass
class ExperimentInfo:
    num_messages: int
    df: pd.DataFrame


def publish_by_number(
    waku_clients: Dict[str, client.WakuClient], messages_per_node: int
):
    """
    The specific publishing scenario for this experiment.

    This function instructs every node in the network to publish a
    specified number of messages concurrently.
    """
    logger.info(
        f"Publishing {messages_per_node} messages from each of the {len(waku_clients)} nodes..."
    )

    publish_tasks = []
    for node_id, waku_client in waku_clients.items():
        for i in range(messages_per_node):
            msg = client.create_waku_message(
                payload=f"msg-{i}-{node_id}", content_topic=CONTENT_TOPIC
            )
            publish_tasks.append((waku_client, msg))

    with ThreadPoolExecutor() as executor:
        list(
            executor.map(
                lambda task: task[0].publish_message(PUBSUB_TOPIC, task[1]),
                publish_tasks,
            )
        )

    logger.info("All messages published.")


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
    plt.figure(figsize=(12, 8))
    sns.set_theme(style="whitegrid")
    plot = sns.regplot(
        x="total_messages",
        y="net_bandwidth_cost_mb",
        data=summary_df,
        ci=95,
    )
    plot.set_title(
        f"Total Messages Sent vs. Net Bandwidth Cost ({num_nodes} nodes)", fontsize=16
    )
    plot.set_xlabel("Total Number of Messages Sent (across all nodes)", fontsize=12)
    plot.set_ylabel("Net Bandwidth Cost (MB)", fontsize=12)
    plt.savefig(filename)
    plt.close()
    logger.info(f"Aggregate plot saved to {filename}")


def plot_time_series(experiments: list[ExperimentInfo], filename: str):
    # TODO
    pass


def main():
    # TODO: accept cmd args
    logger.info("Starting 'Number of Messages vs. Bandwidth' experiment session.")

    messages_per_node_configs = [1, 2, 4, 8, 16]
    all_experiments = []

    for msg_count in messages_per_node_configs:
        logger.info(f"Running experiment for {msg_count} messages per node...")

        scenario = lambda clients: publish_by_number(clients, msg_count)
        # TODO: bootstrap nodes proporitonal to num of nodes
        raw_df = run_experiment_lifecycle(NUM_NODES, 1, scenario)

        if raw_df.empty:
            logger.warning(f"No data for {msg_count} msgs/node run.")
            continue

        total_messages = msg_count * NUM_NODES
        all_experiments.append(ExperimentInfo(total_messages, raw_df))

    if all_experiments:
        plot_time_series(all_experiments, "results/num_vs_bandwidth_time_series.png")

        analyze_and_plot_aggregate(
            all_experiments, "results/num_vs_bandwidth.png", NUM_NODES
        )

    logger.info("Experiment session finished.")


if __name__ == "__main__":
    logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s")
    main()
