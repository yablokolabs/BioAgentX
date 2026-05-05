import logging


def configure_logging(level: str = "INFO") -> None:
    """Configure root logger with structured log format.

    Safe to call multiple times — existing handlers are removed first to
    guarantee the requested *level* and *format* take effect.
    """
    root = logging.getLogger()
    root.handlers.clear()
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="ts=%(asctime)s level=%(levelname)s logger=%(name)s message=%(message)s",
        force=True,
    )
