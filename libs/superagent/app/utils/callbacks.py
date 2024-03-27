from __future__ import annotations

import asyncio
import logging
from typing import Any, AsyncIterator, List, Literal, Tuple, Union, cast

from decouple import config
from langchain.callbacks.base import AsyncCallbackHandler
from langchain.schema.agent import AgentFinish
from langchain.schema.output import LLMResult
from langfuse import Langfuse
from litellm import cost_per_token, token_counter

logger = logging.getLogger(__name__)


class CustomAsyncIteratorCallbackHandler(AsyncCallbackHandler):
    """Callback handler that returns an async iterator."""

    queue: asyncio.Queue[str]

    done: asyncio.Event

    TIMEOUT_SECONDS = 60
    is_stream_started = False

    @property
    def always_verbose(self) -> bool:
        return True

    def __init__(self) -> None:
        self.queue = asyncio.Queue(maxsize=5)
        self.done = asyncio.Event()

    async def on_agent_finish(self, finish: AgentFinish, **_: Any) -> Any:
        """Run on agent end."""
        # This is for the tools whose return_direct property is set to True
        if not self.is_stream_started:
            output = finish.return_values["output"]
            for token in output.split("\n"):
                await self.on_llm_new_token(token + "\n")

            while not self.queue.empty():
                await asyncio.sleep(0.1)
            self.done.set()

    async def on_llm_start(self, *_: Any, **__: Any) -> None:
        # If two calls are made in a row, this resets the state
        self.done.clear()

    async def on_llm_new_token(self, token: str, **kwargs: Any) -> None:  # noqa
        if token is not None and token != "":
            has_put = False
            while not has_put:
                try:
                    await self.queue.put(token)
                    has_put = True
                except asyncio.QueueFull:
                    continue

    async def on_llm_end(self, response, **kwargs: Any) -> None:  # noqa
        # TODO:
        # This should be removed when Langchain has merged
        # https://github.com/langchain-ai/langchain/pull/9536
        for gen_list in response.generations:
            for gen in gen_list:
                if gen.message.content != "":
                    self.done.set()

    async def on_llm_error(self, *args: Any, **kwargs: Any) -> None:  # noqa
        self.done.set()

    async def aiter(self) -> AsyncIterator[str]:
        while not self.queue.empty() or not self.done.is_set():
            done, pending = await asyncio.wait(
                [
                    asyncio.ensure_future(self.queue.get()),
                    asyncio.ensure_future(self.done.wait()),
                ],
                return_when=asyncio.FIRST_COMPLETED,
                timeout=self.TIMEOUT_SECONDS,
            )
            if not done:
                logger.warning(
                    f"{self.TIMEOUT_SECONDS} seconds of timeout reached")
                self.done.set()
                break

            for future in pending:
                future.cancel()

            token_or_done = cast(
                Union[str, Literal[True]], done.pop().result())

            if token_or_done is True:
                continue
            self.is_stream_started = True
            yield token_or_done


class CostCalcAsyncHandler(AsyncCallbackHandler):
    """Callback handler that calculates the cost of the prompt and completion."""

    def __init__(self, model):
        self.model = model
        self.prompt: str = ""
        self.completion: str = ""
        self.prompt_tokens: int = 0
        self.completion_tokens: int = 0
        self.prompt_tokens_cost_usd: float = 0.0
        self.completion_tokens_cost_usd: float = 0.0

    def on_llm_start(self, _, prompts: List[str], **kwargs: Any) -> None:  # noqa
        self.prompt = prompts[0]

    def on_llm_end(self, llm_result: LLMResult, **kwargs: Any) -> None:  # noqa
        self.completion = llm_result.generations[0][0].message.content
        completion_tokens = self._calculate_tokens(self.completion)
        prompt_tokens = self._calculate_tokens(self.prompt)

        (
            prompt_tokens_cost_usd,
            completion_tokens_cost_usd,
        ) = self._calculate_cost_per_token(prompt_tokens, completion_tokens)

        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.prompt_tokens_cost_usd = prompt_tokens_cost_usd
        self.completion_tokens_cost_usd = completion_tokens_cost_usd

    def _calculate_tokens(self, text: str) -> int:
        return token_counter(model=self.model, text=text)

    def _calculate_cost_per_token(
        self, prompt_tokens: int, completion_tokens: int
    ) -> Tuple[float, float]:
        return cost_per_token(
            model=self.model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )


def get_session_tracker_handler(
    workflow_id,
    agent_id,
    session_id,
    user_id,
):
    langfuse_secret_key = config("LANGFUSE_SECRET_KEY", "")
    langfuse_public_key = config("LANGFUSE_PUBLIC_KEY", "")
    langfuse_host = config("LANGFUSE_HOST", "https://cloud.langfuse.com")
    langfuse_handler = None
    if langfuse_public_key and langfuse_secret_key:
        langfuse = Langfuse(
            public_key=langfuse_public_key,
            secret_key=langfuse_secret_key,
            host=langfuse_host,
            sdk_integration="Superagent",
        )
        trace = langfuse.trace(
            id=session_id,
            name="Workflow",
            tags=[agent_id],
            metadata={"agentId": agent_id, "workflowId": workflow_id},
            user_id=user_id,
            session_id=workflow_id,
        )
        langfuse_handler = trace.get_langchain_handler()
        return langfuse_handler

    return None
