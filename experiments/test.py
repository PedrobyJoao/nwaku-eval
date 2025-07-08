import logging
import sys
import time
from mesh.mesh import Mesh

# Configuration for the test
NUM_NODES = 5
BOOTSTRAPPERS_NUM = 1
# Using a recent nwaku image version.
IMAGE_NAME = "wakuorg/nwaku:v0.19.0"
SLEEP_DURATION = 30  # seconds


def main():
    logging.info("Starting mesh test experiment...")

    try:
        with Mesh(
            num_nodes=NUM_NODES,
            bootstrappers_num=BOOTSTRAPPERS_NUM,
            image_name=IMAGE_NAME,
        ) as mesh:
            logging.info(
                f"Mesh with {len(mesh.bootstrap_nodes)} bootstrap nodes and "
                f"{len(mesh.nodes)} regular nodes is running."
            )
            logging.info(f"Sleeping for {SLEEP_DURATION} seconds...")
            time.sleep(SLEEP_DURATION)
            logging.info(f"Finished sleeping.")

    except Exception as e:
        logging.error(f"An error occurred during the experiment: {e}", exc_info=True)
        sys.exit(1)

    logging.info(
        "Mesh test experiment finished. The 'with' block has exited, "
        "and all resources should have been cleaned up."
    )


if __name__ == "__main__":
    main()
