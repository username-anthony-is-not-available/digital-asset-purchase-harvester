import logging
from unittest.mock import MagicMock, patch
from digital_asset_harvester.telemetry.logging_utils import (
    StructuredLoggerAdapter,
    StructuredLoggerFactory,
)

def test_structured_logger_adapter_processes_with_extra():
    mock_logger = MagicMock()
    adapter = StructuredLoggerAdapter(mock_logger, {"test": "test"})
    msg, kwargs = adapter.process("test message", {"extra": {"test2": "test2"}})
    assert kwargs["extra"] == {"extra_test": "test", "test2": "test2"}

def test_structured_logger_factory_builds_adapter():
    factory = StructuredLoggerFactory(json_output=False)
    adapter = factory.build("test_logger")
    assert isinstance(adapter, StructuredLoggerAdapter)

def test_structured_logger_factory_builds_json_adapter():
    factory = StructuredLoggerFactory(json_output=True)
    adapter = factory.build("test_logger")
    assert isinstance(adapter, StructuredLoggerAdapter)

@patch("logging.getLogger")
def test_structured_logger_factory_builds_with_default_fields(mock_get_logger):
    mock_logger = MagicMock()
    mock_get_logger.return_value = mock_logger
    factory = StructuredLoggerFactory(json_output=False)
    adapter = factory.build("test_logger", default_fields={"test": "test"})
    assert adapter.extra == {"test": "test"}

@patch("json.dumps")
@patch("logging.getLogger")
def test_structured_logger_factory_builds_json_adapter_with_formatter(
    mock_get_logger, mock_dumps
):
    mock_logger = MagicMock()
    mock_logger.handlers = []
    mock_get_logger.return_value = mock_logger

    factory = StructuredLoggerFactory(json_output=True)
    factory.build("test_logger")

    assert mock_logger.addHandler.called
