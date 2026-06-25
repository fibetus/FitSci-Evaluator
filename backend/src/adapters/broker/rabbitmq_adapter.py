from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable

import aio_pika
from aio_pika.abc import AbstractChannel, AbstractRobustConnection

from ...domain.errors import QueueError
from ...domain.ports.logger import LoggerPort, NullLogger
from ...domain.ports.message_queue import MessageQueuePort

EvaluationJobHandler = Callable[[str, str], Awaitable[None]]


class RabbitMQAdapter(MessageQueuePort):
    def __init__(
        self,
        amqp_url: str,
        *,
        queue_name: str,
        logger: LoggerPort | None = None,
        requeue_delay_seconds: float = 1.0,
    ) -> None:
        self._amqp_url = amqp_url
        self._queue_name = queue_name
        self._logger = logger or NullLogger()
        self._requeue_delay_seconds = requeue_delay_seconds
        self._connection: AbstractRobustConnection | None = None
        self._channel: AbstractChannel | None = None

    async def connect(self) -> None:
        if self._connection is not None and not self._connection.is_closed:
            return
        try:
            self._connection = await aio_pika.connect_robust(self._amqp_url)
            self._channel = await self._connection.channel()
            await self._channel.declare_queue(self._queue_name, durable=True)
        except Exception as exc:
            raise QueueError("Failed to connect to RabbitMQ") from exc

    async def close(self) -> None:
        if self._connection is not None and not self._connection.is_closed:
            await self._connection.close()
        self._connection = None
        self._channel = None

    async def publish_evaluation_job(self, job_id: str, pmc_id: str) -> None:
        await self._ensure_channel()
        assert self._channel is not None
        body = json.dumps({"job_id": job_id, "pmc_id": pmc_id}).encode()
        try:
            await self._channel.default_exchange.publish(
                aio_pika.Message(
                    body=body,
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                    content_type="application/json",
                ),
                routing_key=self._queue_name,
            )
        except Exception as exc:
            raise QueueError(f"Failed to publish job {job_id}") from exc
        self._logger.info(
            "evaluation_job_published",
            job_id=job_id,
            pmc_id=pmc_id,
            queue=self._queue_name,
        )

    async def consume_evaluation_jobs(self, handler: EvaluationJobHandler) -> None:
        await self._ensure_channel()
        assert self._channel is not None
        await self._channel.set_qos(prefetch_count=1)
        queue = await self._channel.declare_queue(self._queue_name, durable=True)
        self._logger.info("evaluation_worker_listening", queue=self._queue_name)

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                try:
                    payload = json.loads(message.body.decode())
                    job_id = str(payload["job_id"])
                    pmc_id = str(payload["pmc_id"])
                except (json.JSONDecodeError, UnicodeDecodeError, KeyError) as exc:
                    # Poison message: never processable, drop it instead of looping.
                    await message.reject(requeue=False)
                    self._logger.error("evaluation_job_malformed", error=str(exc))
                    continue

                try:
                    await handler(job_id, pmc_id)
                except Exception as exc:
                    # Transient failure (e.g. Ollama/DB unavailable): requeue and keep
                    # consuming. The brief delay avoids hot-looping on a stuck message.
                    await message.nack(requeue=True)
                    self._logger.error(
                        "evaluation_job_requeued", job_id=job_id, error=str(exc)
                    )
                    if self._requeue_delay_seconds > 0:
                        await asyncio.sleep(self._requeue_delay_seconds)
                    continue

                await message.ack()

    async def _ensure_channel(self) -> None:
        if self._channel is None or self._channel.is_closed:
            await self.connect()
