"""MCP-compliant logging configuration for Vista API MCP Server"""

import json
import logging
import logging.handlers
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastmcp.utilities.logging import (
    Console,
    RichHandler,
)
from fastmcp.utilities.logging import (
    get_logger as fastmcp_get_logger,
)

_CONFIGURED_LOGGERS: set[str] = set()

# Ensure logs directory exists
Path("logs").mkdir(exist_ok=True)


class HIPAAFormatter(logging.Formatter):
    """JSON formatter with HIPAA-compliant data masking"""

    def __init__(self, debug_mode: bool = False):
        super().__init__()
        self.debug_mode = debug_mode
        # Patterns for sensitive data
        self.ssn_pattern = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
        self.dfn_pattern = re.compile(r"\b[A-Z]{2}\d{6}\b")
        self.ip_pattern = re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b")
        self.nine_digit_pattern = re.compile(r"\b\d{9}\b")

    def mask_sensitive_data(self, text: str) -> str:
        """Mask sensitive data in log messages"""
        if not text or self.debug_mode:
            return text

        # Mask SSNs
        text = self.ssn_pattern.sub("[REDACTED-SSN]", text)

        # Mask DFNs (2 letters + 6 digits)
        text = self.dfn_pattern.sub("[REDACTED-DFN]", text)

        # Mask IP addresses
        text = self.ip_pattern.sub("[REDACTED-IP]", text)

        # Mask 9-digit numbers (potential SSNs)
        text = self.nine_digit_pattern.sub("[REDACTED-9DIGIT]", text)

        return text

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON with HIPAA compliance"""
        # Create structured log entry
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": self.mask_sensitive_data(record.getMessage()),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add extra fields if present
        if hasattr(record, "rpc_name"):
            log_entry["rpc_name"] = record.rpc_name
        if hasattr(record, "station"):
            log_entry["station"] = record.station
        if hasattr(record, "duz"):
            log_entry["duz"] = record.duz
        if hasattr(record, "success"):
            log_entry["success"] = record.success
        if hasattr(record, "duration_ms"):
            log_entry["duration_ms"] = record.duration_ms
        if hasattr(record, "operation"):
            log_entry["operation"] = record.operation
        if hasattr(record, "user_id"):
            log_entry["user_id"] = record.user_id
        if hasattr(record, "action"):
            log_entry["action"] = record.action
        if hasattr(record, "patient_dfn"):
            log_entry["patient_dfn"] = "[REDACTED-PATIENT]"

        # Add any other extra attributes
        for key, value in record.__dict__.items():
            if key not in [
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "getMessage",
                "exc_info",
                "exc_text",
                "stack_info",
                "rpc_name",
                "station",
                "duz",
                "success",
                "duration_ms",
                "operation",
                "user_id",
                "action",
                "patient_dfn",
            ]:
                log_entry[key] = value

        return json.dumps(log_entry)


def _create_formatter() -> HIPAAFormatter:
    debug_mode = os.getenv("VISTA_MCP_DEBUG", "false").lower() in [
        "true",
        "1",
        "yes",
    ]
    return HIPAAFormatter(debug_mode=debug_mode)


def get_logger(name: str = "mcp-server") -> logging.Logger:
    """Get a logger configured for MCP compliance"""
    logger = fastmcp_get_logger(name)

    if name in _CONFIGURED_LOGGERS:
        return logger

    # Set log level
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logger.setLevel(getattr(logging, log_level, logging.INFO))

    # Create formatter
    formatter = _create_formatter()

    disable_file_logging = os.getenv("DISABLE_FILE_LOGGING", "false").lower() in [
        "true",
        "1",
        "yes",
    ]

    if not disable_file_logging:
        log_file = os.getenv("LOG_FILE", "logs/octo-vista.log")
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Console handler (disabled by default for MCP compliance)
    enable_console = os.getenv("ENABLE_CONSOLE_LOGGING", "false").lower() in [
        "true",
        "1",
        "yes",
    ]
    if enable_console:
        console_handler = RichHandler(
            console=Console(stderr=True),
            rich_tracebacks=True,
            markup=False,
            enable_link_path=False,
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    logger.propagate = False
    _CONFIGURED_LOGGERS.add(name)

    return logger


def log_mcp_message(server_instance, level: str, message: str, **kwargs) -> None:
    """Send log message through MCP protocol (when available)"""
    try:
        if (
            hasattr(server_instance, "request_context")
            and server_instance.request_context
        ):
            server_instance.request_context.session.send_log_message(
                level=level, data=message, **kwargs
            )
    except Exception:
        # Fall back to regular logging if MCP logging fails
        logger = get_logger("mcp-server")
        log_func = getattr(logger, level.lower(), logger.info)
        log_func(message, extra=kwargs)


def log_with_context(
    logger: logging.Logger, level: str, message: str, **kwargs
) -> None:
    """Log message with structured context"""
    log_func = getattr(logger, level.lower(), logger.info)
    log_func(message, extra=kwargs)


def log_rpc_call(
    logger: logging.Logger,
    rpc_name: str,
    station: str,
    duz: str,
    duration_ms: int | None = None,
    success: bool = True,
    error: str | None = None,
    parameters: list[dict[str, Any]] | None = None,
    **kwargs,
) -> None:
    """Log RPC call with structured data"""
    # Check debug mode to determine if parameters should be logged
    debug_mode = os.getenv("VISTA_MCP_DEBUG", "false").lower() in ["true", "1", "yes"]

    log_data = {
        "rpc": rpc_name,
        "station": station,
        "duz": duz,
        "timestamp": datetime.now(UTC).isoformat(),
        "success": success,
        **kwargs,
    }

    if duration_ms is not None:
        log_data["duration_ms"] = duration_ms

    if error:
        log_data["error"] = error

    if debug_mode and parameters:
        log_data["parameters"] = parameters

    if success:
        logger.info(f"RPC call completed: {rpc_name}", extra=log_data)
    else:
        logger.error(f"RPC call failed: {rpc_name}", extra=log_data)


def log_patient_access(
    logger: logging.Logger,
    patient_dfn: str,
    action: str,
    user_duz: str,
    station: str,
    success: bool = True,
    **kwargs,
) -> None:
    """Log patient data access (HIPAA compliant)"""
    # Check debug mode to determine if patient_dfn should be masked
    debug_mode = os.getenv("VISTA_MCP_DEBUG", "false").lower() in ["true", "1", "yes"]

    log_data = {
        "patient_dfn": patient_dfn if debug_mode else "[REDACTED-PATIENT]",
        "action": action,
        "user_duz": user_duz,
        "station": station,
        "success": success,
        **kwargs,
    }

    level = "info" if success else "warning"
    log_with_context(logger, level, f"Patient access: {action}", **log_data)


# Initialize default logger
logger = get_logger()
