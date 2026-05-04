from abc import ABC, abstractmethod

from bioagentx.orchestration.state import AgentStep, WorkflowState


class Agent(ABC):
    name: str

    async def run(self, state: WorkflowState) -> WorkflowState:
        step = state.add_step(AgentStep(agent=self.name, action=self.__class__.__name__))
        step.start()
        output = await self.execute(state)
        step.complete(output)
        state.touch()
        return state

    @abstractmethod
    async def execute(self, state: WorkflowState) -> dict[str, object]: ...
