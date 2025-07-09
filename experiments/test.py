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


NUM_NODES = 5


def do_experiment(num_nodes: int, messages_per_node: int) -> pd.DataFrame:
    """
    Runs a single, isolated experiment and returns the raw time-series data.

    This function is a pure "data producer." It is responsible for
    the complete lifecycle of one experiment run but does not perform
    any analysis itself. It returns all collected metrics as a
    DataFrame.

    Args:
        num_nodes: The number of nodes to include in the mesh.
        messages_per_node: The number of messages each node will publish.

    Returns:
        A pandas DataFrame containing the raw, time-stamped metrics
        collected during the experiment.
    """
    logging.info(
        f"Starting experiment: {num_nodes} nodes, "
        f"{messages_per_node} messages per node."
    )

    # The actual implementation of the experiment phases will go here:
    # 1. `with Mesh(...) as mesh:` to ensure setup and teardown.
    # 2. Polling logic to collect metrics into a list of dicts.
    # 3. `pd.DataFrame(list_of_metrics_polls)` to create the output.

    # For now, we return a placeholder DataFrame to demonstrate structure.
    fake_data = {
        "timestamp": range(10),
        "total_bytes_in": [i * 100 for i in range(10)],
        "total_bytes_out": [i * 200 for i in range(10)],
    }
    raw_data_df = pd.DataFrame(fake_data)

    logging.info("Experiment finished. Returning raw data.")
    return raw_data_df


def plot_time_series(raw_data: pd.DataFrame, filename: str):
    """
    Generates and saves a time-series plot from raw experiment data.

    Args:
        raw_data: DataFrame from do_experiment.
        filename: The path to save the plot image to.
    """
    logging.info(f"Generating time-series plot: {filename}")
    # Implementation will use matplotlib/seaborn to plot bandwidth
    # rate (calculated from diffs in total_bytes) over time.
    pass


def calculate_summary(
    raw_data: pd.DataFrame, num_nodes: int, messages_per_node: int
) -> dict:
    """
    Calculates the summary (aggregate) results from raw experiment data.

    Args:
        raw_data: DataFrame from do_experiment.
        num_nodes: The number of nodes in the experiment.
        messages_per_node: The number of messages each node published.

    Returns:
        A dictionary containing the single summary data point for this
        entire run, ready for final aggregation.
    """
    logging.info("Calculating summary for the run...")
    # Implementation will calculate baseline rate, gross bandwidth,
    # and duration from the raw_data to find the net cost.

    # Placeholder result:
    total_messages = num_nodes * messages_per_node
    # Fake net_bandwidth_cost for structure demonstration
    net_bandwidth_cost = total_messages * 2048

    return {
        "total_messages": total_messages,
        "net_bandwidth_cost": net_bandwidth_cost,
    }


def analyze_and_plot_aggregate(results: list[dict]):
    """
    Analyzes all summary results and generates the final aggregate plot.

    Args:
        results: A list of summary dictionaries, one from each run.
    """
    logging.info("Analyzing all experiment runs and plotting aggregate results...")
    if not results:
        logging.warning("No results to analyze.")
        return

    summary_df = pd.DataFrame(results)

    print("\n--- Experiment Summary ---")
    print(summary_df)
    print("------------------------\n")

    # Full implementation will use matplotlib/seaborn to create and
    # save the final plot from summary_df.
    logging.info("Analysis complete. Aggregate plot would be generated here.")


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

        # 3. Calculate the summary from the raw data.
        summary = calculate_summary(raw_data_df, NUM_NODES, msg_count)
        all_summaries.append(summary)

    # 4. Analyze all collected summaries and make the final plot.
    analyze_and_plot_aggregate(all_summaries)

    logging.info("Bandwidth measurement session finished.")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    main()
