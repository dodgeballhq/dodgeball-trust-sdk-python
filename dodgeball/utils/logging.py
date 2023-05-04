import logging
from logging import Logger, LogRecord

class DodgeballLogger:
    class_logger: Logger = None

    @classmethod
    def get_logger(cls):
        if DodgeballLogger.class_logger is None:
            DodgeballLogger.class_logger = logging.Logger("Dodgeball", logging.WARNING)

        return DodgeballLogger.class_logger

    @classmethod
    def info(cls, msg: str):
        cls.get_logger().info(msg)

    @classmethod
    def warning(cls, msg: str):
        cls.get_logger().warning(msg)

    @classmethod
    def error(cls, msg, *args, **kwargs):
        cls.get_logger().error(msg, args, kwargs)