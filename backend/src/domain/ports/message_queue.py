from typing import Protocol


class MessageQueuePort(Protocol):
    async def publish_evaluation_job(self, job_id: str, pmc_id: str) -> None:
        """Enqueue an evaluation job for background processing."""
        ...
