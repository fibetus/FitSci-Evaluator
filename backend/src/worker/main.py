"""Background worker consuming evaluation jobs from RabbitMQ."""

from __future__ import annotations

import asyncio
import signal
import sys

from ..composition import AppContainer
from ..config import get_settings


async def run_worker() -> None:
    settings = get_settings()
    container = AppContainer(settings, correlation_id="worker")
    await container.startup()

    stop_event = asyncio.Event()

    def _request_stop(*_: object) -> None:
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _request_stop)
        except NotImplementedError:
            signal.signal(sig, lambda *_args: _request_stop())

    worker_task = asyncio.create_task(
        container.queue.consume_evaluation_jobs(container.process_evaluation_job.execute)
    )
    await stop_event.wait()
    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        pass
    await container.shutdown()


def main() -> None:
    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
