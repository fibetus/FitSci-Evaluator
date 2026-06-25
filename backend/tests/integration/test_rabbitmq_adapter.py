import os

import pytest

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("FITSCI_INTEGRATION") != "1",
        reason="Set FITSCI_INTEGRATION=1 to run RabbitMQ integration tests",
    ),
]

pytest.importorskip("testcontainers.rabbitmq")


@pytest.mark.anyio
async def test_rabbitmq_publish_and_consume_roundtrip() -> None:
    from testcontainers.rabbitmq import RabbitMqContainer

    from src.adapters.broker.rabbitmq_adapter import RabbitMQAdapter
    from src.config.settings import Settings

    with RabbitMqContainer("rabbitmq:3.13-management-alpine") as rabbit:
        settings = Settings(
            deployment="local",
            postgres_dsn="postgresql+asyncpg://x:x@localhost/x",
            postgres_sync_dsn="postgresql+psycopg://x:x@localhost/x",
            rabbitmq_url=rabbit.get_connection_url(),
            ollama_base_url="http://localhost:11434",
            gemma_model_tag="gemma4:12b-q4_k_m",
            log_level="INFO",
            rate_limit_per_minute=30,
            ncbi_api_key=None,
            rabbitmq_evaluation_queue="fitsci.test.jobs",
            evaluation_idempotency_hours=24,
        )
        adapter = RabbitMQAdapter(
            settings.rabbitmq_url,
            queue_name=settings.rabbitmq_evaluation_queue,
        )
        received: list[tuple[str, str]] = []

        async def handler(job_id: str, pmc_id: str) -> None:
            received.append((job_id, pmc_id))

        await adapter.connect()
        await adapter.publish_evaluation_job("job-1", "PMC1")

        import asyncio

        consume_task = asyncio.create_task(adapter.consume_evaluation_jobs(handler))
        await asyncio.sleep(1)
        consume_task.cancel()
        try:
            await consume_task
        except asyncio.CancelledError:
            pass
        await adapter.close()

        assert received == [("job-1", "PMC1")]


@pytest.mark.anyio
async def test_rabbitmq_requeues_on_transient_failure() -> None:
    """A handler that raises (transient failure) must NOT lose the message: it is
    nacked + requeued and redelivered to the still-running consumer until it
    succeeds. This is the core resilience guarantee from ADR-0006."""
    import asyncio

    from testcontainers.rabbitmq import RabbitMqContainer

    from src.adapters.broker.rabbitmq_adapter import RabbitMQAdapter

    with RabbitMqContainer("rabbitmq:3.13-management-alpine") as rabbit:
        adapter = RabbitMQAdapter(
            rabbit.get_connection_url(),
            queue_name="fitsci.test.requeue",
            requeue_delay_seconds=0.0,
        )

        attempts: list[str] = []
        succeeded = asyncio.Event()

        async def flaky_handler(job_id: str, pmc_id: str) -> None:
            attempts.append(job_id)
            if len(attempts) < 3:
                raise RuntimeError("transient failure (e.g. Ollama down)")
            succeeded.set()

        await adapter.connect()
        await adapter.publish_evaluation_job("job-flaky", "PMC1")

        consume_task = asyncio.create_task(
            adapter.consume_evaluation_jobs(flaky_handler)
        )
        try:
            await asyncio.wait_for(succeeded.wait(), timeout=15)
        finally:
            consume_task.cancel()
            try:
                await consume_task
            except asyncio.CancelledError:
                pass
            await adapter.close()

        # Redelivered after each transient failure; consumer stayed alive.
        assert len(attempts) >= 3
        assert succeeded.is_set()


@pytest.mark.anyio
async def test_rabbitmq_drops_malformed_message_without_requeue_loop() -> None:
    """A malformed payload is a poison message: it must be rejected (dropped),
    not requeued forever. A valid message published afterwards must still flow."""
    import asyncio

    import aio_pika
    from testcontainers.rabbitmq import RabbitMqContainer

    from src.adapters.broker.rabbitmq_adapter import RabbitMQAdapter

    with RabbitMqContainer("rabbitmq:3.13-management-alpine") as rabbit:
        url = rabbit.get_connection_url()
        queue_name = "fitsci.test.poison"
        adapter = RabbitMQAdapter(url, queue_name=queue_name, requeue_delay_seconds=0.0)
        received: list[tuple[str, str]] = []
        got_valid = asyncio.Event()

        async def handler(job_id: str, pmc_id: str) -> None:
            received.append((job_id, pmc_id))
            got_valid.set()

        await adapter.connect()

        # Publish a malformed (non-JSON) message directly, bypassing the adapter.
        raw_conn = await aio_pika.connect_robust(url)
        raw_channel = await raw_conn.channel()
        await raw_channel.default_exchange.publish(
            aio_pika.Message(body=b"not-json"), routing_key=queue_name
        )
        await raw_conn.close()

        consume_task = asyncio.create_task(adapter.consume_evaluation_jobs(handler))
        await adapter.publish_evaluation_job("job-good", "PMC2")
        try:
            await asyncio.wait_for(got_valid.wait(), timeout=15)
        finally:
            consume_task.cancel()
            try:
                await consume_task
            except asyncio.CancelledError:
                pass
            await adapter.close()

        assert received == [("job-good", "PMC2")]
