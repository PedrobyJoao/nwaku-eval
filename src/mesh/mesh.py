import docker
import logging
import requests
import time

from .utils import get_free_ports, new_docker_net, pull_docker_image

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from docker import errors
from docker.models.containers import Container
from docker.models.images import Image
from docker.models.networks import Network
from requests.exceptions import ConnectionError, HTTPError

DOCKER_NET_NAME = "p2p-eval-test"

# Logger will be inherited by Mesh consumers
# TODO: debug level parametrizable
# TODO: should we modularize logger? I don't think that is necessary for such a POC
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)


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
            logging.info(f"Stopped and removed container: {self.container.name}")
        except errors.NotFound:
            logging.warning(
                f"Container {self.container.name} not found for cleanup, already removed."
            )
        except Exception as e:
            logging.error(f"Error cleaning up container {self.container.name}: {e}")


class Mesh:
    """
    Mesh handles the setup and teardown of a mesh network of nodes.

    Notes:
    1. Currently it creates a docker network and runs all nodes in it.
    2. There is no discovery yet

    TODOs:
    - [ ] deployment and teardown of nodes in parallel
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
        """Returns the list of bootstrap nodes in the mesh."""
        return self._bootstrap_nodes

    @property
    def regular_nodes(self) -> list[NodeContainer]:
        """Returns the list of regular nodes in the mesh."""
        return self._nodes

    @property
    def all_nodes(self) -> list[NodeContainer]:
        return self._bootstrap_nodes + self._nodes

    def start(self):
        """
        Starts the mesh network:
        1. creates a docker network
        2. starts bootstrap nodes and retrieve their listening addresses
        3. starts regular nodes
        """
        logging.info("Starting mesh...")
        self._image = pull_docker_image(self._client, self._image_name)
        self._network = new_docker_net(self._client, DOCKER_NET_NAME)

        logging.info(f"Starting {self._bootstrappers_num} bootstrap nodes...")
        for i in range(self._bootstrappers_num):
            # TODO: set all ports beforehand so that we can deploy nodes in parallel later
            rest_port, metrics_port = get_free_ports(2)
            node = self._start_node(f"bootstrap-node-{i}", rest_port, metrics_port)
            self._bootstrap_nodes.append(node)

        bootstrap_multiaddrs = [
            self._get_multiaddr(node) for node in self._bootstrap_nodes
        ]

        num_regular_nodes = self._num_nodes - self._bootstrappers_num
        logging.info(f"Starting {num_regular_nodes} regular nodes...")
        for i in range(num_regular_nodes):
            rest_port, metrics_port = get_free_ports(2)
            node = self._start_node(
                f"node-{i}",
                rest_port,
                metrics_port,
                bootstrap_multiaddresses=bootstrap_multiaddrs,
            )
            self._nodes.append(node)

        logging.info("Mesh started successfully.")

    def stop(self):
        """Stops and removes all containers and the network."""
        logging.info("Stopping mesh...")
        with ThreadPoolExecutor() as executor:
            # TODO: handle exceptions here?
            executor.map(lambda node: node.cleanup(), self.all_nodes)

        if self._network:
            try:
                self._network.remove()
                logging.info(f"Removed network: {self._network.name}")
            except errors.APIError as e:
                logging.error(f"Error removing network {self._network.name}: {e}")

        self._bootstrap_nodes.clear()
        self._nodes.clear()
        logging.info("Mesh stopped.")

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
            ports={
                f"{rest_port}/tcp": rest_port,
                f"{metrics_port}/tcp": metrics_port,
            },
            network=self._network.name,
        )
        logging.info(
            f"Started container: {name} with REST port {rest_port} and metrics port {metrics_port}"
        )

        return NodeContainer(name, container, rest_port, metrics_port)

    def _get_multiaddr(
        self, node: NodeContainer, retries: int = 10, delay: float = 1.0
    ) -> str:
        """
        Retrieves the multiaddress of a node by querying its REST API with retries.
        This handles the race condition where the API is not yet ready.

        TODO: use waku client
        TODO: is getting the first elem from the listenAddresses reliable enough?
        """
        api_url = f"http://localhost:{node.rest_port}/info"
        for i in range(retries):
            try:
                response = requests.get(api_url, timeout=1)
                response.raise_for_status()
                info = response.json()
                multiaddr = info["listenAddresses"][0]
                logging.debug(f"Got multiaddr for {node.container.name}: {multiaddr}")
                return multiaddr
            except (ConnectionError, HTTPError, requests.exceptions.ReadTimeout) as e:
                logging.debug(
                    f"Attempt {i+1}/{retries}: Could not get multiaddr for {node.container.name}, retrying... Error: {e}"
                )
                time.sleep(delay)

        raise Exception(f"Could not get multiaddr for {node.container.name}")
