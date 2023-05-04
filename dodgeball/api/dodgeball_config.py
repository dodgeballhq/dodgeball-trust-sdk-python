from logging import Logger
from ..utils.logging import DodgeballLogger


class DodgeballConfig:
    def __init__(self,
                api_url: str,
                is_enabled: bool = True,
                api_version: str = None,
                logger: Logger = None):
        self.apiUrl = api_url
        self.isEnabled = is_enabled
        self.apiVersion = api_version
        if logger:
            DodgeballLogger.class_logger = logger
