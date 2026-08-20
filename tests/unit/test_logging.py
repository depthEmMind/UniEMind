import json
import logging

from observability import JSONFormatter


def test_json_formatter_includes_trace_context() -> None:
    formatter = JSONFormatter()
    record = logging.LogRecord("test", logging.INFO, "", 0, "ready", (), None)
    record.trace_id = "trace-1"
    payload = json.loads(formatter.format(record))
    assert payload["event"] == "ready"
    assert payload["trace_id"] == "trace-1"
