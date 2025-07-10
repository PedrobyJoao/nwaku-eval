import docker
import logging
import requests
import time

from .utils import get_free_ports, new_docker_net, pull_docker_image
from nwaku.client import WakuRestClient

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from docker import errors
from docker.models.containers import Container
from docker.models.images import Image
from docker.models.networks import Network
from requests.exceptions import ConnectionError, HTTPError

DOCKER_NET_NAME = "p2p-eval-test"

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


@dataclass
class NodeContainer:
    """Holds state for a running node container."""

    id: str
    container: Container
    rest_port: int
    metrics_port: int

    def cleanup(self):
        try:
            self.container.stop()
            self.container.remove()
            logger.info(f"Stopped and removed container: {self.container.name}")
        except errors.NotFound:
            logger.warning(
                f"Container {self.container.name} not found for cleanup, already removed."
            )
        except Exception as e:
            logger.error(f"Error cleaning up container {self.container.name}: {e}")


class Mesh:
    """
    Mesh handles the setup and teardown of a network of nodes.

    1. Currently it creates a docker network and runs all nodes in it.
    2. There is no discovery yet

    TODOs:
    - [ ] statically build mesh or add discovery
    - [ ] handle forceful shutdown signals
    - [ ] allow building image too
    - [ ] allow arbitrary p2p apps
        - [ ] required: receive necessary ports flags to run application
    """

    def __init__(self, num_nodes: int, bootstrappers_num: int, image_name: str):
        if bootstrappers_num >= num_nodes:
            raise ValueError("Total nodes must be greater than bootstrap nodes.")

        self._num_nodes = num_nodes
        self._bootstrappers_num = bootstrappers_num
        self._image_name = image_name
        self._client = docker.from_env()
        self._image: Image | None = None
        self._network: Network | None = None
        self._bootstrap_nodes: list[NodeContainer] = []
        self._nodes: list[NodeContainer] = []

    @property
    def bootstrap_nodes(self) -> list[NodeContainer]:
        return self._bootstrap_nodes

    @property
    def regular_nodes(self) -> list[NodeContainer]:
        """Returns the list of non-bootstrap nodes in the mesh."""
        return self._nodes

    @property
    def all_nodes(self) -> list[NodeContainer]:
        return self._bootstrap_nodes + self._nodes

    def start(self):
        """
        Starts the mesh network concurrently:
        1. Pre-allocates all necessary ports.
        2. Starts bootstrap nodes concurrently.
        3. Fetches their multiaddresses concurrently.
        4. Starts regular nodes concurrently.

        TODO: node configs shouldn't be built with dicts but instead with a dataclass
        """
        logger.info("Starting mesh: pulling image and creating docker network")
        self._image = pull_docker_image(self._client, self._image_name)
        self._network = new_docker_net(self._client, DOCKER_NET_NAME)

        # 1. Pre-allocate all ports at once to avoid race conditions
        logger.debug("Pre-allocating ports...")
        num_ports_needed = self._num_nodes * 2
        all_ports = get_free_ports(num_ports_needed)
        port_iterator = iter(all_ports)

        # 2. Prepare startup configs for all nodes
        bootstrap_configs = []
        for i in range(self._bootstrappers_num):
            bootstrap_configs.append(
                {
                    "name": f"bootstrap-node-{i}",
                    "rest_port": next(port_iterator),
                    "metrics_port": next(port_iterator),
                }
            )

        regular_node_configs = []
        for i in range(self._num_nodes - self._bootstrappers_num):
            regular_node_configs.append(
                {
                    "name": f"node-{i}",
                    "rest_port": next(port_iterator),
                    "metrics_port": next(port_iterator),
                }
            )

        # 3. Start bootstrap nodes
        logger.info(f"Starting {self._bootstrappers_num} bootstrap nodes...")
        with ThreadPoolExecutor() as executor:
            self._bootstrap_nodes = list(
                executor.map(lambda cfg: self._start_node(**cfg), bootstrap_configs)
            )

        # 4. Get multiaddresses
        logger.info("Getting multiaddresses of bootstrap nodes...")
        with ThreadPoolExecutor() as executor:
            bootstrap_multiaddrs = list(
                executor.map(self._get_multiaddr, self._bootstrap_nodes)
            )

        # 5. Start non-bootstrap nodes
        num_regular_nodes = self._num_nodes - self._bootstrappers_num
        logger.info(f"Starting {num_regular_nodes} regular nodes...")
        with ThreadPoolExecutor() as executor:
            self._nodes = list(
                executor.map(
                    lambda cfg: self._start_node(
                        **cfg, bootstrap_multiaddresses=bootstrap_multiaddrs
                    ),
                    regular_node_configs,
                )
            )

        logger.info("Mesh started successfully.")

    def stop(self):
        """Stops and removes all containers and the network."""
        logger.info("Stopping mesh...")
        with ThreadPoolExecutor() as executor:
            # TODO: handle exceptions here?
            list(executor.map(lambda node: node.cleanup(), self.all_nodes))

        if self._network:
            try:
                self._network.remove()
                logger.info(f"Removed network: {self._network.name}")
            except errors.APIError as e:
                logger.error(f"Error removing network {self._network.name}: {e}")

        self._bootstrap_nodes.clear()
        self._nodes.clear()
        logger.info("Mesh stopped.")

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def _start_node(
        self,
        name: str,
        rest_port: int,
        metrics_port: int,
        bootstrap_multiaddresses: list[str] | None = None,
    ) -> NodeContainer:
        """Starts a single node container with required ports and config."""
        if not self._network:
            raise ValueError("Network not initialized.")

        if not self._image:
            raise ValueError("Image not initialized.")

        command = [
            f"--listen-address=0.0.0.0",
            f"--rest=true",
            f"--rest-admin=true",
            f"--rest-address=0.0.0.0",
            f"--rest-port={rest_port}",
            f"--metrics-server=true",
            f"--metrics-server-address=0.0.0.0",
            f"--metrics-server-port={metrics_port}",
        ]
        if bootstrap_multiaddresses:
            for addr in bootstrap_multiaddresses:
                if addr:
                    command.append(f"--staticnode={addr}")

        container = self._client.containers.run(
            self._image,
            command=command,
            name=name,
            detach=True,
            # make node's APIs accessible to host, and therefore to this script'
            ports={
                f"{rest_port}/tcp": rest_port,
                f"{metrics_port}/tcp": metrics_port,
            },
            network=self._network.name,
        )
        logger.info(
            f"Started container: {name} with REST port {rest_port} and metrics port {metrics_port}"
        )

        return NodeContainer(name, container, rest_port, metrics_port)

    def _get_multiaddr(self, node: NodeContainer) -> str:
        with WakuRestClient(
            ip_address="localhost",
            rest_port=node.rest_port,
            metrics_port=node.metrics_port,
        ) as client:
            info = client.get_info()
            listen_addrs = info.get("listenAddresses", [])
            if not listen_addrs:
                raise Exception(f"Node {node.id} reported no listen addresses")

            # find first not loopback since we're using docker network
            for addr in listen_addrs:
                if "/127.0.0.1/" not in addr:
                    logger.debug(f"Selected multiaddr for {node.id}: {addr}")
                    return addr

            raise Exception(f"Could not find a non-loopback multiaddr for {node.id}")
