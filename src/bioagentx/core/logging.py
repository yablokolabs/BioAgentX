import logging


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="ts=%(asctime)s level=%(levelname)s logger=%(name)s message=%(message)s",
    )
