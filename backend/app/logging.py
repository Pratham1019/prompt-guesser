import json
import logging
import sys
from datetime import datetime, timezone

from app.config import settings


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs structured JSON logs in production
    and readable, colored-like text logs in development.
    """

    def format(self, record: logging.LogRecord) -> str:
        # Create standard structured log payload
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "func_name": record.funcName,
            "line_no": record.lineno,
        }

        # Format exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Include custom extra parameters passed via extra={"key": "val"}
        # by filtering out standard LogRecord attributes
        extra_fields = {
            k: v
            for k, v in record.__dict__.items()
            if k
            not in {
                "args",
                "asctime",
                "created",
                "exc_info",
                "exc_text",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "msg",
                "name",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "stack_info",
                "thread",
                "threadName",
            }
        }
        if extra_fields:
            log_data["extra"] = extra_fields

        # Format output depending on the environment
        if settings.ENVIRONMENT == "development":
            exc_str = f"\n{log_data['exception']}" if "exception" in log_data else ""
            extra_str = f" | extra: {log_data['extra']}" if "extra" in log_data else ""
            location = f"{log_data['module']}.{log_data['func_name']}:{log_data['line_no']}"
            return (
                f"[{log_data['timestamp']}] {log_data['level']:<5} | "
                f"{log_data['message']} (in {location}){extra_str}{exc_str}"
            )

        return json.dumps(log_data, default=str)


def setup_logging() -> None:
    """
    Configures root logging handler with the StructuredFormatter and sets the log level.
    """
    root_logger = logging.getLogger()

    # Avoid duplicate handlers if setup_logging is called multiple times
    if root_logger.handlers:
        for handler in list(root_logger.handlers):
            root_logger.removeHandler(handler)

    # Set up console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredFormatter())

    root_logger.addHandler(handler)

    # Resolve log level from settings
    log_level_str = settings.LOG_LEVEL.upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    root_logger.setLevel(log_level)

    # Silence noisy external libraries a bit in development/production
    logging.getLogger("uvicorn.access").handlers = [handler]
    logging.getLogger("uvicorn.error").handlers = [handler]

    # Prevent uvicorn default handlers from duplicating log output
    logging.getLogger("uvicorn.access").propagate = False
    logging.getLogger("uvicorn.error").propagate = False

    # Route SQLAlchemy logs through our structured handler
    sql_logger = logging.getLogger("sqlalchemy.engine")
    sql_logger.handlers = [handler]
    sql_logger.propagate = False
    # Only print queries in DEBUG environment settings
    if log_level_str == "DEBUG":
        sql_logger.setLevel(logging.INFO)
    else:
        sql_logger.setLevel(logging.WARNING)


# Auto-configure logging upon import
setup_logging()
logger = logging.getLogger("app")
