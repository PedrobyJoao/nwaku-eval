import base64
import functools
import urllib.parse
import logging
import time
from typing import Any

import requests


class WakuRestClientException(Exception):
    """Base exception for WakuRestClient errors."""

    pass


def with_retry(attempts: int = 10, delay: float = 1.0):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            last_exception = None
            for i in range(attempts):
                try:
                    return func(self, *args, **kwargs)
                except (
                    requests.exceptions.RequestException,
                    WakuRestClientException,
                ):
                    if i < attempts - 1:
                        time.sleep(delay)
            raise WakuRestClientException(
                f"Request {func.__name__} failed after {attempts} attempts: {last_exception}"
            ) from last_exception

        return wrapper

    return decorator


class WakuRestClient:
    """
    A simple HTTP client for the NWaku REST API.

    This client provides methods to interact with a nwaku node's
    REST API for subscribing to topics, publishing messages, retrieving
    messages, and getting node information. It uses a requests.Session
    for connection pooling and provides helpers for message creation.
    """

    def __init__(self, ip_address: str, rest_port: int, timeout: int = 10):
        self.base_url = f"http://{ip_address}:{rest_port}"
        self.session = requests.Session()
        self.timeout = timeout
        logging.info(f"WakuRestClient initialized for {self.base_url}")

    def close(self):
        """Closes the underlying requests session."""
        self.session.close()
        logging.debug(f"WakuRestClient session closed for {self.base_url}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _handle_response(self, response: requests.Response) -> requests.Response:
        try:
            response.raise_for_status()
            return response
        except requests.exceptions.HTTPError as e:
            url = e.response.url
            logging.error(f"HTTP Error: {e.response.status_code} for {url}")
            logging.error(f"Response body: {e.response.text}")
            raise WakuRestClientException(f"HTTP Error: {e}") from e

    @with_retry()
    def get_info(self) -> dict[str, Any]:
        """
        Retrieves information about the running nwaku node.
        Corresponds to GET /info.
        """
        url = f"{self.base_url}/info"
        headers = {"accept": "application/json"}
        response = self.session.get(url, headers=headers, timeout=self.timeout)
        return self._handle_response(response).json()

    @with_retry()
    def subscribe_to_pubsub_topic(self, pubsub_topics: list[str]) -> requests.Response:
        """
        Subscribes to one or more pubsub topics.
        Corresponds to POST /relay/v1/subscriptions.
        """
        url = f"{self.base_url}/relay/v1/subscriptions"
        headers = {"accept": "text/plain", "content-type": "application/json"}
        response = self.session.post(
            url, headers=headers, json=pubsub_topics, timeout=self.timeout
        )
        return self._handle_response(response)

    @with_retry()
    def publish_message(self, topic: str, message: dict[str, Any]) -> requests.Response:
        """
        Publishes a message to a pubsub topic.
        Corresponds to POST /relay/v1/messages/{pubsubTopic}.
        """
        encoded_topic = urllib.parse.quote_plus(topic)
        url = f"{self.base_url}/relay/v1/messages/{encoded_topic}"
        headers = {"content-type": "application/json"}
        response = self.session.post(
            url, headers=headers, json=message, timeout=self.timeout
        )
        return self._handle_response(response)

    @with_retry()
    def get_messages(self, topic: str) -> list[dict[str, Any]]:
        """
        Retrieves messages from a pubsub topic. This is a polling endpoint.
        Corresponds to GET /relay/v1/messages/{pubsubTopic}.
        """
        encoded_topic = urllib.parse.quote_plus(topic)
        url = f"{self.base_url}/relay/v1/messages/{encoded_topic}"
        headers = {"accept": "application/json"}
        response = self.session.get(url, headers=headers, timeout=self.timeout)
        return self._handle_response(response).json()


def create_waku_message(
    payload: str,
    content_topic: str,
    ephemeral: bool = True,
    meta: str | None = None,
) -> dict[str, Any]:
    """
    This helper handles base64 encoding for the payload and meta fields
    and sets the current timestamp in nanoseconds.
    """
    message = {
        "payload": base64.b64encode(payload.encode("utf-8")).decode("utf-8"),
        "contentTopic": content_topic,
        "timestamp": int(time.time_ns()),
        "ephemeral": ephemeral,
    }
    if meta:
        message["meta"] = base64.b64encode(meta.encode("utf-8")).decode("utf-8")
    return message
