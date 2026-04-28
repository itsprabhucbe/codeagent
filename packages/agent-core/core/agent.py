class Agent:
    """Main agent orchestrator."""

    def __init__(self, model: str = "claude-sonnet-4-20250514"):
        self.model = model

    async def run(self, task: str) -> str:
        raise NotImplementedError
