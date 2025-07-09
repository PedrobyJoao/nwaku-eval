import pytest

from nwaku.client import scrape_metrics

METRICS_DUMP_PATH = "src/nwaku/tests/metrics_dump.txt"


@pytest.fixture(scope="session")
def metrics_dump() -> str:
    with open(METRICS_DUMP_PATH, "r") as f:
        return f.read()


def test_scrape_libp2p_network_bytes_total(metrics_dump: str):
    metric_name = "libp2p_network_bytes_total"
    results = scrape_metrics(metrics_dump, metric_name)
    assert len(results) == 2

    # Sort for predictable order
    results.sort(key=lambda x: x["labels"]["direction"])

    assert results[0]["labels"] == {"direction": "in"}
    assert results[0]["value"] == 5055.0
    assert results[1]["labels"] == {"direction": "out"}
    assert results[1]["value"] == 3918.0


def test_scrape_metric_with_no_labels(metrics_dump: str):
    metric_name = "libp2p_peers"
    results = scrape_metrics(metrics_dump, metric_name)
    assert len(results) == 1
    assert results[0] == {"labels": {}, "value": 1.0}


def test_scrape_metric_not_found(metrics_dump: str):
    metric_name = "this_metric_does_not_exist"
    results = scrape_metrics(metrics_dump, metric_name)
    assert len(results) == 0


def test_scrape_on_empty_input():
    results = scrape_metrics("", "any_metric")
    assert results == []


def test_scrape_with_malformed_lines():
    malformed_metrics = """
# HELP some_metric help text
# TYPE some_metric gauge
some_metric{label="value"} not_a_float
another_metric just_a_value_no_name
{label="no_name"} 1.0
metric_no_space_or_value
"""
    results = scrape_metrics(malformed_metrics, "some_metric")
    assert results == []
