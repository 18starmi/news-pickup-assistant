import asyncio
import logging

from app.db.session import get_connection
from app.services.scheduler_service import SchedulerService


logger = logging.getLogger(__name__)


class BackgroundSchedulerRunner:
    def __init__(self, poll_seconds: int = 30) -> None:
        self.poll_seconds = poll_seconds
        self._task: asyncio.Task | None = None
        self._stop_event = asyncio.Event()

    def start(self) -> None:
        if self._task is not None:
            return
        self._stop_event.clear()
        self._task = asyncio.create_task(self._run_loop())

    async def stop(self) -> None:
        if self._task is None:
            return
        self._stop_event.set()
        await self._task
        self._task = None

    async def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                ran = await asyncio.to_thread(self._run_once)
                if ran:
                    logger.info("Scheduled pipeline run completed")
            except Exception:  # noqa: BLE001
                logger.exception("Scheduled pipeline run failed")
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=self.poll_seconds)
            except TimeoutError:
                continue

    @staticmethod
    def _run_once() -> bool:
        with get_connection() as connection:
            return SchedulerService(connection).run_due_job()
