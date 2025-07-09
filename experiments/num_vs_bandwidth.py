"""
Number of messages <-> Bandwidth

This script addresses the problem of understanding how bandwidth
usage in a Waku network is affected by the number of messages
being sent. It creates a decentralized, many-to-many traffic
pattern where all nodes in the network publish messages
concurrently.

The analysis is presented through two primary visualizations:
1.  A Time-Series Plot: For each individual experiment run, this
    plot shows the bandwidth rate (bytes/sec) over time. It
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

A: For scientific rigor and clarity. By setting up a fresh,
   clean network for each set of parameters (e.g., for 10
   messages, then for 20, etc.), we ensure that each run is an
   independent, controlled experiment. This allows us to
   isolate the impact of our single variable (number of
   messages) on bandwidth.

   A single, long experiment with sequential batches would
   introduce conflicting variables. The network state (e.g.,
   peer scores, caches) from the first batch would influence
   the results of the second, making it difficult to attribute
   any changes in bandwidth cost solely to the change in
   message count. Our isolated-run approach provides a much
   cleaner and more defensible answer to the core question.
"""

import logging

import pandas as pd

from mesh.mesh import Mesh
from nwaku import client


NUM_NODES = 5


def do_experiment(num_nodes: int, messages_per_node: int) -> pd.DataFrame:
    """
    Runs a single, isolated experiment and returns a dataframe.

    This function is a pure "data producer." It is responsible for
    the complete lifecycle of one experiment run but does not perform
    any analysis itself.

    Experiment on the high-level:
    1. Setup mesh
        1. create mesh
        2. subscribe all nodes to the same topic
    2. Polling libp2p bytes total metrics to stabilish baseline
    of an idle node
        1. get the result and stop polling
    3. start polling again
    4. publish `n` messages from each peer `p`
    # what else should we do AI?


    """
    logging.info(
        f"Starting experiment: {num_nodes} nodes, "
        f"{messages_per_node} messages per node."
    )


def plot_time_series(raw_data: pd.DataFrame, filename: str):
    logging.info(f"Generating time-series plot: {filename}")
    pass


def analyze_and_plot_aggregate(results: list[dict]):
    pass


def main():
    """
    Main function to orchestrate the entire experiment session.
    """
    logging.info("Starting bandwidth measurement session.")

    messages_per_node_configs = [1, 5, 10, 20, 50]
    all_summaries = []

    for msg_count in messages_per_node_configs:
        # 1. Run one isolated experiment to get the raw data.
        raw_data_df = do_experiment(num_nodes=NUM_NODES, messages_per_node=msg_count)

        # 2. Generate the diagnostic time-series plot for this run.
        run_name = f"{NUM_NODES}nodes_{msg_count}msgs"
        plot_time_series(raw_data_df, f"timeseries_{run_name}.png")

    # 4. Analyze all collected summaries and make the final plot.
    analyze_and_plot_aggregate(all_summaries)

    logging.info("Bandwidth measurement session finished.")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    main()
