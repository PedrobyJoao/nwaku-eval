import docker
import logging
import requests

from .utils import get_free_ports, new_docker_net, pull_docker_image

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from docker import errors
from docker.models.containers import Container
from docker.models.images import Image
from docker.models.networks import Network
from requests.exceptions import ConnectionError

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

        self.num_nodes = num_nodes
        self.bootstrappers_num = bootstrappers_num
        self.image_name = image_name
        self.client = docker.from_env()
        self.image: Image | None = None
        self.network: Network | None = None
        self.bootstrap_nodes: list[NodeContainer] = []
        self.nodes: list[NodeContainer] = []

    def start(self):
        """
        Starts the mesh network:
        1. creates a docker network
        2. starts bootstrap nodes and retrieve their listening addresses
        3. starts regular nodes
        """
        logging.info("Starting mesh...")
        self.image = pull_docker_image(self.client, self.image_name)
        self.network = new_docker_net(self.client, DOCKER_NET_NAME)

        logging.info(f"Starting {self.bootstrappers_num} bootstrap nodes...")
        for i in range(self.bootstrappers_num):
            # TODO: set all ports beforehand so that we can deploy nodes in parallel later
            rest_port, metrics_port = get_free_ports(2)
            node = self._start_node(f"bootstrap-node-{i}", rest_port, metrics_port)
            self.bootstrap_nodes.append(node)

        bootstrap_multiaddrs = [
            self._get_multiaddr(node) for node in self.bootstrap_nodes
        ]

        num_regular_nodes = self.num_nodes - self.bootstrappers_num
        logging.info(f"Starting {num_regular_nodes} regular nodes...")
        for i in range(num_regular_nodes):
            rest_port, metrics_port = get_free_ports(2)
            node = self._start_node(
                f"node-{i}",
                rest_port,
                metrics_port,
                bootstrap_multiaddresses=bootstrap_multiaddrs,
            )
            self.nodes.append(node)

        logging.info("Mesh started successfully.")

    def stop(self):
        """Stops and removes all containers and the network."""
        logging.info("Stopping mesh...")
        all_nodes = self.bootstrap_nodes + self.nodes
        with ThreadPoolExecutor() as executor:
            # TODO: handle exceptions here?
            executor.map(lambda node: node.cleanup(), all_nodes)

        if self.network:
            try:
                self.network.remove()
                logging.info(f"Removed network: {self.network.name}")
            except errors.APIError as e:
                logging.error(f"Error removing network {self.network.name}: {e}")

        self.bootstrap_nodes.clear()
        self.nodes.clear()
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
        if not self.network:
            raise ValueError("Network not initialized.")

        if not self.image:
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
                command.append(f"--staticnode={addr}")

        container = self.client.containers.run(
            self.image,
            command=command,
            name=name,
            detach=True,
            ports={
                f"{rest_port}/tcp": rest_port,
                f"{metrics_port}/tcp": metrics_port,
            },
            network=self.network.name,
        )
        logging.info(
            f"Started container: {name} with REST port {rest_port} and metrics port {metrics_port}"
        )
        return NodeContainer(container, rest_port, metrics_port)

    def _get_multiaddr(self, node: NodeContainer) -> str:
        """Retrieves the multiaddress of a node by querying its REST API."""
        # TODO: with retries?
        try:
            api_url = f"http://127.0.0.1:{node.rest_port}/info"
            response = requests.get(api_url)
            response.raise_for_status()
            info = response.json()
            multiaddr = info["listenAddresses"][
                0
            ]  # TODO: maybe a more reliable way of retrieving from json?
            logging.debug(f"Got multiaddr for {node.container.name}: {multiaddr}")
            return multiaddr

        except (ConnectionError, requests.exceptions.HTTPError) as e:
            logging.debug(f"Error getting multiaddr for {node.container.name}: {e}")
            return ""  # TODO: do we have to return None in Pyhton instead?
