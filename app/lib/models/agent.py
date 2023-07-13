from pydantic import BaseModel


class Agent(BaseModel):
    name: str
    type: str
    llm: dict = None
    hasMemory: bool = False
    memorySize: int = 3
    promptId: str = None
    maxTokens: int = 1024
    temperature: float = 0


class PredictAgent(BaseModel):
    input: dict
    has_streaming: bool = False
