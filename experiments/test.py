import logging
import random
import sys
import time

from mesh.mesh import Mesh
from waku_client import WakuRestClient, create_waku_message

NUM_NODES = 5
BOOTSTRAPPERS_NUM = 1
IMAGE_NAME = "wakuorg/nwaku"
MESSAGE_COUNT = 10


def main():
    logging.info("Starting bandwidth measurement experiment.")

    pubsub_topic = "waku/2/default-waku/proto"
    content_topic = "/my-app/1/my-topic/proto"

    try:
        with Mesh(
            num_nodes=NUM_NODES,
            bootstrappers_num=BOOTSTRAPPERS_NUM,
            image_name=IMAGE_NAME,
        ) as mesh:
            num_boot = len(mesh.bootstrap_nodes)
            num_reg = len(mesh.regular_nodes)
            logging.info(f"Mesh running: {num_boot} bootstrap, {num_reg} regular.")

            # Allow time for nodes to establish connections
            logging.info("Waiting for nodes to connect and stabilize...")
            time.sleep(10)

            # Subscribe all nodes to the pubsub topic
            logging.info(f"Subscribing all nodes to pubsub topic: {pubsub_topic}...")
            for node in mesh.all_nodes:
                with WakuRestClient("127.0.0.1", node.rest_port) as client:
                    client.subscribe_to_pubsub_topic([pubsub_topic])

            # Wait for subscriptions to propagate
            time.sleep(20)

            # Select a random publisher and create a client for it
            publisher_node = random.choice(mesh.all_nodes)
            logging.info(f"Using node {publisher_node.container.name} as publisher.")

            with WakuRestClient(
                "127.0.0.1", publisher_node.rest_port
            ) as publisher_client:
                logging.info(f"Publishing {MESSAGE_COUNT} messages...")
                for i in range(MESSAGE_COUNT):
                    payload = f"Hello from message {i}"
                    msg = create_waku_message(payload, content_topic)
                    publisher_client.publish_message(
                        topic=pubsub_topic,
                        message=msg,
                    )
                logging.info(f"Published {MESSAGE_COUNT} messages successfully.")

            logging.info("Waiting for messages to propagate...")
            time.sleep(10)

    except Exception as e:
        logging.error("Experiment failed: %s", e, exc_info=True)
        sys.exit(1)

    logging.info("Experiment finished. Cleanup complete.")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    main()
