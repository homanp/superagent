# flake8: noqa
import json
from typing import Any, Tuple

from slugify import slugify
from decouple import config
from langchain import HuggingFaceHub
from langchain.agents import Tool, create_csv_agent, AgentType
from langchain.chains import RetrievalQA
from langchain.chat_models import (
    AzureChatOpenAI,
    ChatAnthropic,
    ChatOpenAI,
)
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.llms import Cohere, OpenAI
from langchain.memory import ChatMessageHistory, ConversationBufferMemory
from langchain.prompts.prompt import PromptTemplate
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain.schema import SystemMessage

from app.lib.callbacks import StreamingCallbackHandler
from app.lib.models.document import DocumentInput
from app.lib.models.tool import (
    SearchToolInput,
    WolframToolInput,
    ReplicateToolInput,
    ZapierToolInput,
    AgentToolInput,
    OpenApiToolInput,
)
from app.lib.prisma import prisma
from app.lib.prompts import (
    CustomPromptTemplate,
    DEFAULT_CHAT_PROMPT,
    DEFAULT_AGENT_PROMPT,
)
from app.lib.tools import (
    ToolDescription,
    get_search_tool,
    get_wolfram_alpha_tool,
    get_replicate_tool,
    get_zapier_nla_tool,
    get_openapi_tool,
    AgentTool,
    DocSummarizerTool,
)
from app.lib.vectorstores.base import VectorStoreBase


class AgentBase:
    def __init__(
        self,
        agent: dict,
        api_key: str = None,
        has_streaming: bool = False,
        on_llm_new_token=None,
        on_llm_end=None,
        on_chain_end=None,
    ):
        self.id = agent.id
        self.api_key = api_key
        self.userId = agent.userId
        self.document = agent.document
        self.has_memory = agent.hasMemory
        self.memory_size = agent.memorySize
        self.max_tokens = agent.maxTokens
        self.temperature = agent.temperature
        self.type = agent.type
        self.llm = agent.llm
        self.prompt = agent.prompt
        self.tool = agent.tool
        self.has_streaming = has_streaming
        self.on_llm_new_token = on_llm_new_token
        self.on_llm_end = on_llm_end
        self.on_chain_end = on_chain_end
        self.documents = self._get_agent_documents()
        self.tools = self._get_agent_tools()

    def _get_api_key(self) -> str:
        if self.llm["provider"] == "openai-chat" or self.llm["provider"] == "openai":
            return (
                self.llm["api_key"]
                if "api_key" in self.llm
                else config("OPENAI_API_KEY")
            )

        if self.llm["provider"] == "anthropic":
            return (
                self.llm["api_key"]
                if "api_key" in self.llm
                else config("ANTHROPIC_API_KEY")
            )

        if self.llm["provider"] == "cohere":
            return (
                self.llm["api_key"]
                if "api_key" in self.llm
                else config("COHERE_API_KEY")
            )

        if self.llm["provider"] == "azure-openai":
            return (
                self.llm["api_key"]
                if "api_key" in self.llm
                else config("AZURE_API_KEY")
            )

        if self.llm["provider"] == "huggingface":
            return (
                self.llm["api_key"]
                if "api_key" in self.llm
                else config("HUGGINGFACEHUB_API_TOKEN")
            )

    def _get_prompt(self, tools: list = None) -> Any:
        if not self.tools and not self.documents:
            if (
                self.llm["provider"] == "openai-chat"
                or self.llm["provider"] == "azure-openai"
            ):
                system_message_prompt = SystemMessagePromptTemplate.from_template(
                    template=self.prompt.template
                    if self.prompt
                    else DEFAULT_CHAT_PROMPT.template
                )
                return ChatPromptTemplate(
                    input_variables=self.prompt.input_variables
                    if self.prompt
                    else DEFAULT_CHAT_PROMPT.input_variables,
                    messages=[system_message_prompt],
                )
            return (
                PromptTemplate(
                    input_variables=self.prompt.input_variables,
                    template=self.prompt.template,
                )
                if self.prompt
                else DEFAULT_CHAT_PROMPT
            )

        if self.type == "REACT":
            return CustomPromptTemplate(
                template=self.prompt.template if self.prompt else DEFAULT_AGENT_PROMPT,
                tools=tools,
                input_variables=["input", "intermediate_steps", "chat_history"],
            )

        if self.type == "OPENAI":
            return SystemMessage(content=self.prompt.template) if self.prompt else None

        return DEFAULT_CHAT_PROMPT

    def _get_llm(self, has_streaming: bool = True) -> Any:
        if self.llm["provider"] == "openai-chat":
            return (
                ChatOpenAI(
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    openai_api_key=self._get_api_key(),
                    model_name=self.llm["model"],
                    streaming=self.has_streaming,
                    callbacks=[
                        StreamingCallbackHandler(
                            agent_type=self.type,
                            on_llm_new_token_=self.on_llm_new_token,
                            on_llm_end_=self.on_llm_end,
                            on_chain_end_=self.on_chain_end,
                        ),
                    ],
                )
                if self.has_streaming and has_streaming != False
                else ChatOpenAI(
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    model_name=self.llm["model"],
                    openai_api_key=self._get_api_key(),
                )
            )

        if self.llm["provider"] == "openai":
            return OpenAI(
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                model_name=self.llm["model"],
                openai_api_key=self._get_api_key(),
            )

        if self.llm["provider"] == "anthropic":
            return (
                ChatAnthropic(
                    streaming=self.has_streaming,
                    anthropic_api_key=self._get_api_key(),
                    callbacks=[
                        StreamingCallbackHandler(
                            agent_type=self.type,
                            on_llm_new_token_=self.on_llm_new_token,
                            on_llm_end_=self.on_llm_end,
                            on_chain_end_=self.on_chain_end,
                        )
                    ],
                )
                if self.has_streaming and has_streaming != False
                else ChatAnthropic(anthropic_api_key=self._get_api_key())
            )

        if self.llm["provider"] == "cohere":
            return (
                Cohere(
                    cohere_api_key=self._get_api_key(),
                    model=self.llm["model"],
                    callbacks=[
                        StreamingCallbackHandler(
                            agent_type=self.type,
                            on_llm_new_token_=self.on_llm_new_token,
                            on_llm_end_=self.on_llm_end,
                            on_chain_end_=self.on_chain_end,
                        )
                    ],
                )
                if self.has_streaming and has_streaming != False
                else Cohere(cohere_api_key=self._get_api_key(), model=self.llm["model"])
            )

        if self.llm["provider"] == "azure-openai":
            return (
                AzureChatOpenAI(
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    openai_api_key=self._get_api_key(),
                    openai_api_base=config("AZURE_API_BASE"),
                    openai_api_type=config("AZURE_API_TYPE"),
                    openai_api_version=config("AZURE_API_VERSION"),
                    deployment_name=self.llm["model"],
                    streaming=self.has_streaming,
                    callbacks=[
                        StreamingCallbackHandler(
                            agent_type=self.type,
                            on_llm_new_token_=self.on_llm_new_token,
                            on_llm_end_=self.on_llm_end,
                            on_chain_end_=self.on_chain_end,
                        )
                    ],
                )
                if self.has_streaming
                else AzureChatOpenAI(
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    deployment_name=self.llm["model"],
                    openai_api_key=self._get_api_key(),
                    openai_api_base=config("AZURE_API_BASE"),
                    openai_api_type=config("AZURE_API_TYPE"),
                    openai_api_version=config("AZURE_API_VERSION"),
                )
            )

        if self.llm["provider"] == "huggingface":
            return HuggingFaceHub(
                repo_id=self.llm["model"], huggingfacehub_api_token=self._get_api_key()
            )

        # Use ChatOpenAI as default llm in agents
        return ChatOpenAI(temperature=0, openai_api_key=self._get_api_key())

    def _get_memory(self) -> Any:
        history = ChatMessageHistory()

        if self.has_memory:
            memories = prisma.agentmemory.find_many(
                where={"agentId": self.id},
                order={"createdAt": "desc"},
                take=self.memory_size,
            )
            memories = memories[::-1]

            [
                history.add_ai_message(memory.message)
                if memory.author == "AI"
                else history.add_user_message(memory.message)
                for memory in memories
            ]

            if (self.documents or self.tools) and self.type == "OPENAI":
                return ConversationBufferMemory(
                    chat_memory=history,
                    memory_key="chat_history",
                    output_key="output",
                    return_messages=True,
                )

            return ConversationBufferMemory(
                chat_memory=history,
                memory_key="chat_history",
                output_key="output",
            )

        return ConversationBufferMemory(memory_key="chat_history", output_key="output")

    def _get_agent_documents(self) -> Any:
        agent_documents = prisma.agentdocument.find_many(
            where={"agentId": self.id}, include={"document": True}
        )

        return agent_documents

    def _get_tool_and_input_by_type(
        self, type: str, metadata: dict = None
    ) -> Tuple[Any, Any]:
        if type == "SEARCH":
            return get_search_tool(), SearchToolInput
        if type == "WOLFRAM_ALPHA":
            return get_wolfram_alpha_tool(), WolframToolInput
        if type == "REPLICATE":
            return get_replicate_tool(metadata=metadata), ReplicateToolInput
        if type == "ZAPIER_NLA":
            return (
                get_zapier_nla_tool(
                    metadata=metadata, llm=self._get_llm(has_streaming=False)
                ),
                ZapierToolInput,
            )
        if type == "AGENT":
            return (
                AgentTool(metadata=metadata, api_key=self.api_key),
                AgentToolInput,
            )
        if type == "OPENAPI":
            return (get_openapi_tool(metadata=metadata), OpenApiToolInput)

    def _get_tools(self) -> list:
        tools = []
        embeddings = OpenAIEmbeddings()

        for agent_document in self.documents:
            description = (
                f"useful for finding information about {agent_document.document.name}"
            )
            args_schema = DocumentInput if self.type == "OPENAI" else None
            embeddings = OpenAIEmbeddings()
            docsearch = (
                VectorStoreBase()
                .get_database()
                .from_existing_index(embeddings, agent_document.document.id)
            )
            summary_tool = DocSummarizerTool(
                docsearch=docsearch, llm=self._get_llm(has_streaming=False)
            )

            if agent_document.document.type == "CSV":
                csv_agent = create_csv_agent(
                    llm=self._get_llm(has_streaming=False),
                    path=agent_document.document.url,
                    verbose=True,
                    agent_type=AgentType.OPENAI_FUNCTIONS
                    if self.type == "OPENAI"
                    else AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                )
                tools.append(
                    Tool(
                        name=slugify(agent_document.document.name),
                        description=description,
                        args_schema=args_schema,
                        func=csv_agent.run,
                    )
                )
            else:
                tools.append(
                    Tool(
                        name=slugify(agent_document.document.name)
                        if self.type == "OPENAI"
                        else agent_document.document.name,
                        description=description,
                        args_schema=args_schema,
                        func=RetrievalQA.from_chain_type(
                            llm=self._get_llm(has_streaming=False),
                            retriever=docsearch.as_retriever(),
                        ),
                    )
                )
                tools.append(
                    Tool.from_function(
                        func=summary_tool.run,
                        name="document-summarizer",
                        description="useful for summarizing a whole document",
                    )
                )

        for agent_tool in self.tools:
            tool, args_schema = self._get_tool_and_input_by_type(
                agent_tool.tool.type, metadata=agent_tool.tool.metadata
            )
            tools.append(
                Tool(
                    name=slugify(agent_tool.tool.name),
                    description=agent_tool.tool.description
                    or ToolDescription[agent_tool.tool.type].value,
                    args_schema=args_schema if self.type == "OPENAI" else None,
                    func=tool.run if agent_tool.tool.type != "REPLICATE" else tool,
                )
            )

        return tools

    def _get_agent_tools(self) -> Any:
        tools = prisma.agenttool.find_many(
            where={"agentId": self.id}, include={"tool": True}
        )

        return tools

    def _format_trace(self, trace: Any) -> dict:
        if self.documents or self.tools:
            return json.dumps(
                {
                    "output": trace.get("output") or trace.get("result"),
                    "steps": [
                        {
                            "action": step[0].tool,
                            "input": step[0].tool_input,
                            "log": step[0].log,
                            "observation": step[1],
                        }
                        for step in trace["intermediate_steps"]
                    ],
                }
            )

        return json.dumps(
            {
                "output": trace.get("output") or trace.get("result"),
                "steps": [trace],
            }
        )

    def process_payload(self, payload):
        if isinstance(payload, dict):
            if self.type == "OPENAI":
                payload = str(payload)

        return payload

    def create_agent_memory(self, agentId: str, author: str, message: str):
        prisma.agentmemory.create(
            {
                "author": author,
                "message": message,
                "agentId": agentId,
            }
        )

    def save_intermediate_steps(self, trace: dict) -> None:
        prisma.agenttrace.create(
            {
                "userId": self.userId,
                "agentId": self.id,
                "data": trace,
            }
        )

    def get_agent(self) -> Any:
        pass
