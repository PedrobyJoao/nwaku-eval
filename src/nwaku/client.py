import base64
import functools
import urllib.parse
import logging
import time
from typing import Any

import requests

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class WakuRestClientException(Exception):
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
                ) as e:
                    last_exception = e
                    if i < attempts - 1:
                        time.sleep(delay)
            raise WakuRestClientException(
                f"Request {func.__name__} failed after {attempts} attempts: {last_exception}"
            ) from last_exception

        return wrapper

    return decorator


class WakuRestClient:
    """
    A HTTP client for a NWaku node's REST API and metrics endpoint.
    """

    def __init__(
        self,
        ip_address: str,
        rest_port: int,
        metrics_port: int,
        timeout: int = 10,
    ):
        self.base_url = f"http://{ip_address}:{rest_port}"
        self.metrics_url = f"http://{ip_address}:{metrics_port}/metrics"
        self.session = requests.Session()
        self.timeout = timeout
        logger.info(
            f"WakuRestClient initialized for REST API at {self.base_url} "
            f"and metrics at {self.metrics_url}"
        )

    def close(self):
        self.session.close()
        logger.debug(f"WakuRestClient session closed for {self.base_url}")

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
            logger.error(f"HTTP Error: {e.response.status_code} for {url}")
            logger.error(f"Response body: {e.response.text}")
            raise WakuRestClientException(f"HTTP Error: {e}") from e

    @with_retry()
    def get_info(self) -> dict[str, Any]:
        """
        GET /info.
        """
        url = f"{self.base_url}/info"
        headers = {"accept": "application/json"}
        response = self.session.get(url, headers=headers, timeout=self.timeout)
        return self._handle_response(response).json()

    @with_retry()
    def subscribe_to_pubsub_topic(self, pubsub_topics: list[str]) -> requests.Response:
        """
        POST /relay/v1/subscriptions.
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
        POST /relay/v1/messages/{pubsubTopic}.
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
        GET /relay/v1/messages/{pubsubTopic}.
        """
        encoded_topic = urllib.parse.quote_plus(topic)
        url = f"{self.base_url}/relay/v1/messages/{encoded_topic}"
        headers = {"accept": "application/json"}
        response = self.session.get(url, headers=headers, timeout=self.timeout)
        return self._handle_response(response).json()

    @with_retry(attempts=3, delay=0.5)
    def get_metrics(self) -> str:
        """
        GET /metrics
        """
        headers = {"accept": "text/plain"}
        response = self.session.get(
            self.metrics_url, headers=headers, timeout=self.timeout
        )
        return self._handle_response(response).text


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
        "timestamp": time.time_ns(),
        "ephemeral": ephemeral,
    }
    if meta:
        message["meta"] = base64.b64encode(meta.encode("utf-8")).decode("utf-8")
    return message


def scrape_metrics(metrics_raw: str, metric_name: str) -> list[dict]:
    parsed_results = []
    for line in metrics_raw.splitlines():
        if line.startswith("#") or not line.strip():
            continue

        try:
            # The value is always the last part after a space
            name_part, value_str = line.rsplit(" ", 1)
            value = float(value_str)

            brace_pos = name_part.find("{")
            if brace_pos == -1:  # Metric has no labels
                if name_part == metric_name:
                    parsed_results.append({"labels": {}, "value": value})
            else:
                # Metric has labels
                # Check if the part before the brace is our metric
                actual_name = name_part[:brace_pos]
                if actual_name == metric_name:
                    labels = {}
                    # Get the string inside the braces
                    label_str = name_part[brace_pos + 1 : -1]
                    for pair in label_str.split(","):
                        key, val_str = pair.split("=", 1)
                        # Remove quotes from the value string
                        labels[key.strip()] = val_str.strip().strip('"')
                    parsed_results.append({"labels": labels, "value": value})
        except ValueError:
            # This can happen if rsplit fails or float conversion fails.
            # We can safely ignore these lines.
            logger.debug(f"Could not parse metric line: '{line}'")
            continue
    return parsed_results
