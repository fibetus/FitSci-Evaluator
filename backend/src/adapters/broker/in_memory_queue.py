from __future__ import annotations

from ...domain.ports.message_queue import MessageQueuePort


class InMemoryMessageQueue(MessageQueuePort):
    def __init__(self) -> None:
        self.messages: list[tuple[str, str]] = []

    async def publish_evaluation_job(self, job_id: str, pmc_id: str) -> None:
        self.messages.append((job_id, pmc_id))
