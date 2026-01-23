import logging
import signal
from types import FrameType as Frametype

logger = logging.getLogger(__name__)


class SignalHandler:
    def __init__(self)-> None:
        self.signal_received = False
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)

    def _handle_signal(self, signum: int, _frame: Frametype | None) -> None:
        logger.info("Received signal %d, initiating graceful shutdown...", signum)
        self.signal_received = True
