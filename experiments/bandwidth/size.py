"""
Message Size <-> Bandwidth

Design Decisions:
-----------------------
Q: Why use a single publisher instead of many?

A: To create a clean, isolated signal. This experiment aims to
   measure the specific cost of propagating a message of size X.
   Using a single source makes the cause-and-effect relationship
   clearer and a more controlled trial

Q: Why send a batch of messages instead of just one?

A: For statistical reliability. By sending a small, fixed batch of
   messages (e.g., 20) for each size test, we average out random,
   one-off network fluctuations, leading to a more stable and
   trustworthy measurement for each payload size
"""

from dataclasses import dataclass
import logging
import random
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
CONTENT_TOPIC = "size-vs-bw-content-topic"
NUM_MESSAGES_PER_RUN = 20

# How many times the same experiment should be run
NUM_TRIALS = 3


@dataclass
class ExperimentInfo:
    total_payload_size: int
    df: pd.DataFrame


def publish_by_size(
    waku_clients: Dict[str, client.WakuClient],
    payload_size_bytes,
    num_messages: int,
):
    """
    This function randomly selects a single node to publish a fixed
    batch of messages, each with the specified payload size.
    """
    publisher_id = random.choice(list(waku_clients.keys()))
    publisher_client = waku_clients[publisher_id]
    logger.info(
        f"Publishing {num_messages} messages with payload size "
        f"{payload_size_bytes} bytes from single publisher: {publisher_id}"
    )

    # Prepare all tasks for the single publisher
    payload = "a" * payload_size_bytes  # `a` == 1 byte
    messages_to_publish = [
        client.create_waku_message(payload=payload, content_topic=CONTENT_TOPIC)
        for _ in range(num_messages)
    ]

    # Publish the batch concurrently
    with ThreadPoolExecutor() as executor:
        list(
            executor.map(
                lambda msg: publisher_client.publish_message(PUBSUB_TOPIC, msg),
                messages_to_publish,
            )
        )

    logger.info("All messages for this run have been published.")


def analyze_and_plot_aggregate(
    experiments: list[ExperimentInfo], filename: str, num_nodes: int
):
    logger.info(f"Analyzing and plotting aggregate results to {filename}...")
    plot_data = []
    for experiment in experiments:
        df = experiment.df
        agg_df = df.groupby(["node", "direction"])["total_bytes"].agg(["max", "min"])
        net_bandwidth_cost = (agg_df["max"] - agg_df["min"]).sum()
        plot_data.append(
            {
                "total_payload_size_kb": experiment.total_payload_size / 1024,
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
        x="total_payload_size_kb",
        y="net_bandwidth_cost_mb",
        data=summary_df,
        ci=95,
    )
    plot.set_title(
        f"Total Payload Size vs. Net Bandwidth Cost ({num_nodes} nodes)", fontsize=16
    )
    plot.set_xlabel("Total Message Payload Size (KB)", fontsize=12)
    plot.set_ylabel("Net Bandwidth Cost (MB)", fontsize=12)
    plt.savefig(filename)
    plt.close()
    logger.info(f"Aggregate plot saved to {filename}")


def main():
    # TODO: accept cmd args
    logger.info("Starting 'Message Size vs. Bandwidth' experiment session.")

    # The following list is trying to cover a wide range of payload sizes.
    # So that we can both identify what is the network overhead of payloads
    # with small sizes and also the bandwidth relation with msg size as it grows
    # bigger
    #
    # Nwaku message limit: 153600 bytes
    #
    # TODO: library to represent the numbers better
    payload_size_configs = [
        1,  # 1 byte (check y-intercept)
        16,  # 16 bytes
        64,  # 64 bytes
        128,  # 128 bytes
        1 * 1024,  # 1 KB
        8 * 1024,  # 8 KB
        64 * 1024,  # 64 KB
        128 * 1024,  # 128 KB
    ]
    all_experiments = []

    for size_bytes in payload_size_configs:
        # IMPORTANT: maybe a more reliable way is to run several trials
        # of the same experiment so that we could have more stable results,
        # ignoring fluctuations on the y-axis inherited to external factors
        # (e.g.: host machine running the experiment using more CPU, and for
        # some reason nim-libp2p starts to decrease bandwidth usage and increase delay)
        #
        # To implement this, we just have to uncomment the following line:
        # Note: the overall experiment would take longer obviously.
        # for trial in range(NUM_TRIALS):
        logger.info(f"Running experiment for payload size: {size_bytes} bytes...")
        action = lambda clients: publish_by_size(
            clients, size_bytes, NUM_MESSAGES_PER_RUN
        )
        # TODO: bootstrap nodes proporitonal to num of nodes
        raw_df = run_experiment_lifecycle(NUM_NODES, 2, action)

        if raw_df.empty:
            logger.warning(f"No data for {size_bytes} byte run.")
            continue

        # analysis should consider the sum of all messages published
        # in one experiment
        total_payload_size = size_bytes * NUM_MESSAGES_PER_RUN
        all_experiments.append(ExperimentInfo(total_payload_size, raw_df))

    if all_experiments:
        # TODO: time-series here would be good too?
        analyze_and_plot_aggregate(
            all_experiments, "results/size_vs_bandwidth.png", NUM_NODES
        )

    logger.info("Experiment session finished.")


if __name__ == "__main__":
    logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s")
    main()
