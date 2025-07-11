# Introduction and Objectives

This analysis covers how bandwidth of **nwaku's relay protocol** is effected by:

1. Number of messages
2. Message size

It does _not_ cover message rate effect. Thus it should be addressed in a follow-up experiment.

## Methodology

TODO: move the general experimental setup to the main README

A network of nwaku nodes is built as: `n` docker containers within a `d` docker network.
Each docker container runs one nwaku node.

> Docker image: `wakuorg/nwaku` (latest)

Between the `n` nodes, `m` of them are bootstrap nodes.

Both `n` and `m` are arbitrarily chosen by the experiment script.

After the mesh is built, all nodes subscribe to the same pubsub topic.

Then we start polling the metrics from all nodes (concurrently) every 1 second
so that we're the closest to observe all the peaks and valleys of bandwidth usage.

To save time when running the experiments, besides the act of polling the metrics,
the following operations run concurrently: deployment of nodes and
subscription to the pubsub topic.

> Depending on the experiment, it may also publish the messages concurrently as
> it's done on the `number of messages vs bandwidth` experiment.

### Wait times

There are wait times on the following points:

- After creation of the mesh: waiting for network to stabilize and nwaku's APIs to start.
- After subscribing to the pubsub topic: waiting pubsub mesh formation and general
  subscription state to be ready.
- After starting polling metrics: so that we can define a baseline cost of an idle network.
- After publishing messages: just to wait for the messages to arrive at the subscribers.

### Discovery

There is no discovery mechanism added because adding one would extend the duration of the experiments
as they would have to wait longer after the mesh is created to give time for peers to discover each other.

Currently, the experiments wait less than 20 seconds after the mesh is created so that whatever network
processes can stabilize.

> With a discovery mechanism, experiments may have to wait `x` minutes.

### Topology

Since there is no discovery, the current topology is not very realistic since all non-bootstrap peers
are only connected to the bootstrap peers.

Real decentralized networks have more sparse connections between different peers.

Therefore, keeping the experiments duration the shortest possible, the ideal solution is to statically
create the network graph connnecting the peers through API calls.

Though, we would have to make sure no isolated networks (therefore more than one network) are created.

## Metrics

For the bandwidth experiments,`libp2p_network_bytes_total` metrics is used. It's exposed by the
nwaku's metrics endpoint.

This metric is a cumulative counter that captures all libp2p traffic (incoming and outgoing) of a given node.

> There is no reason to differentiate between incoming and outgoing traffic since we want to measure
> the total bandwidth usage. Therefore, we just sum both values.

For both experiments, we calculate the net bandwidth cost throughout the experiment
by subtracting the final bandwidth from the initial bandwidth.

The reason is to eliminate the base network noise not created by the experiment but simply
by nwaku's internal network operations.

## Experiment 1: Message Size vs. Bandwidth

## Experiment 2: Number of Messages vs. Bandwidth

5. Experiment 1: Message Size vs. Bandwidth _ Objective: What specific question does this experiment answer? _ Methodology: _ Publisher Model: Single
   publisher. Explain the rationale (e.g., to create a clean, measurable signal). _ Message Batching: Sent a batch of 20 messages. Explain the rationale
   (e.g., for statistical reliability, to average out network noise). _ Payload Sizes: Logarithmic scale. Explain the rationale (e.g., to efficiently find
   both the fixed overhead and the scaling cost). _ Results & Conclusion: _ Embed the plot (size_vs_bandwidth.png). _ State your main finding (e.g., "a
   strong linear relationship was observed"). _ Explain what the y-intercept of your plot means (the fixed protocol overhead). _ Explain what the slope of
   your plot means (the variable cost per byte).

6. Experiment 2: Number of Messages vs. Bandwidth _ Objective: What specific question does this experiment answer? _ Methodology: _ Publisher Model:
   Many-to-many (all nodes publish). Explain the rationale (e.g., to simulate a more realistic, high-traffic scenario). _ Independent Runs: Fresh network for
   each test. Explain the rationale (e.g., ensures a controlled experiment for each variable). _ Results & Conclusion: _ Embed the plot
   (num*vs_bandwidth.png). * State your main finding (e.g., "bandwidth scales linearly with the number of messages"). \_ Briefly interpret this result (e.g.,
   "the network handles increased load predictably").

## Limitations & Future Work

7. Limitations & Future Work _ Limitations: Be transparent about the experiment's constraints. _ Mention: Ideal network conditions (local Docker), no
   node churn, default GossipSub parameters. _ Future Work: Show you've thought about the next steps. _ Mention: Analyzing delay and message rate, testing
   with larger/more complex networks, tuning GossipSub parameters.
