import docker
import logging
import socket

from contextlib import closing
from docker import errors
from docker.models.images import Image
from docker.models.networks import Network


def new_docker_net(client: docker.DockerClient, name: str) -> Network:
    try:
        existing_network = client.networks.get(name)
        logging.info(f"Removing existing network: {name}")
        existing_network.remove()
    except errors.NotFound:
        pass

    logging.info(f"Creating Docker network: {name}")
    return client.networks.create(name, driver="bridge")


def pull_docker_image(client: docker.DockerClient, image_name: str) -> Image | None:
    try:
        image = client.images.pull(image_name)
        print(f"Successfully pulled {image.tags}")
        return image
    except errors.APIError as e:
        print(f"Error pulling image {image_name}: {e}")
        return None


def get_free_ports(num: int) -> list[int]:
    """Finds a specified number of free TCP ports on the host."""
    # TODO: analyze if that is reliable
    ports = []
    for _ in range(num):
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
            s.bind(("", 0))
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            ports.append(s.getsockname()[1])

    if ports.__len__() != num:
        raise ValueError(f"Failed to find {num} free ports")

    return ports
