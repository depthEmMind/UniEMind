import asyncio

from interaction import ConversationManager, InProcessAPI
from schema import InteractionRequest, InteractionType, Status, Task, TaskStep


def test_in_process_api_runs_task() -> None:
    async def factory(request: InteractionRequest) -> Task:
        return Task(
            session_id=request.session_id,
            goal=request.content,
            steps=[TaskStep(name="noop", skill="speak", inputs={"text": request.content})],
        )

    async def runner(task: Task) -> Task:
        task.status = Status.SUCCESS
        return task

    async def scenario() -> str:
        api = InProcessAPI(ConversationManager(factory, runner))
        payload = await api.post_interaction(
            {
                "session_id": "s1",
                "type": InteractionType.TEXT.value,
                "content": "hello",
            }
        )
        return payload["status"]

    assert asyncio.run(scenario()) == Status.SUCCESS.value
