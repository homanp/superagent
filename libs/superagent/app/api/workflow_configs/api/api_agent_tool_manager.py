# flake8: noqa
import json
import logging

from app.api.agents import (
    add_tool as api_add_agent_tool,
)
from app.api.agents import (
    create as api_create_agent,
)
from app.api.agents import (
    delete as api_delete_agent,
)
from app.api.agents import (
    update as api_update_agent,
)
from app.api.tools import (
    create as api_create_tool,
)
from app.api.tools import (
    delete as api_delete_tool,
)
from app.api.tools import (
    update as api_update_tool,
)
from app.models.request import (
    Agent as AgentRequest,
)
from app.models.request import (
    AgentTool as AgentToolRequest,
)
from app.models.request import (
    AgentUpdate as AgentUpdateRequest,
)
from app.models.request import (
    DatasourceUpdate as DatasourceUpdateRequest,
)
from app.models.request import (
    Tool as ToolRequest,
)
from app.models.request import (
    ToolUpdate as ToolUpdateRequest,
)
from app.utils.prisma import prisma
from prisma.models import Agent as AgentModel
from prisma.enums import ToolType

from .base import BaseApiAgentManager

logger = logging.getLogger(__name__)


class ApiAgentToolManager(BaseApiAgentManager):
    """
    This class is responsible for managing the workflow.
    It provides methods to add, delete, update tools, assistants, and datasources.
    """

    def __init__(self, parent_agent: AgentModel, api_user):
        self.parent_agent = parent_agent
        self.api_user = api_user

    async def get_assistant(self, assistant: dict):
        assistant = AgentUpdateRequest.parse_obj(assistant)

        agent_tools = await prisma.agenttool.find_many(
            where={
                "agentId": self.parent_agent.id,
            },
            include={
                "agent": True,
                "tool": True,
            },
        )

        for agent_tool in agent_tools:
            if agent_tool.tool.name == assistant.name:
                # get agent from tool's metadata agent id
                metadata = json.loads(agent_tool.tool.metadata)
                agent = await prisma.agent.find_first(
                    where={
                        "id": metadata.get("agentId"),
                    }
                )
                return agent

    async def get_tool(self, assistant: dict, tool: dict):
        tool = ToolRequest.parse_obj(tool)
        agent = await self.get_assistant(assistant)
        agent_tools = await prisma.agenttool.find_many(
            where={
                "agentId": agent.id,
            },
            include={
                "tool": True,
            },
        )

        for agent_tool in agent_tools:
            if agent_tool.tool.name == tool.name:
                return agent_tool.tool

    async def get_datasource(self, assistant: dict, datasource: dict):
        datasource = DatasourceUpdateRequest.parse_obj(datasource)
        agent = await self.get_assistant(assistant)

        agent_datasources = await prisma.agentdatasource.find_many(
            where={
                "agentId": agent.id,
            },
            include={
                "datasource": True,
            },
        )

        for agent_datasource in agent_datasources:
            if agent_datasource.datasource.name == datasource.name:
                return agent_datasource.datasource

    async def create_assistant(self, data: dict):
        try:
            res = await api_create_agent(
                body=AgentRequest.parse_obj(data),
                api_user=self.api_user,
            )

            new_agent = res.get("data", {})

            logger.info(f"Created agent: {new_agent}")
            return new_agent
        except Exception as err:
            logger.error(f"Error creating agent: {data} - Error: {err}")

    async def create_tool(self, assistant: dict, data: dict):
        try:
            res = await api_create_tool(
                body=ToolRequest.parse_obj(data),
                api_user=self.api_user,
            )

            new_tool = res.get("data", {})

            logger.info(f"Created tool: {new_tool.name} - {assistant.get('name')}")
            return new_tool
        except Exception as err:
            logger.error(f"Error creating tool: {data} - Error: {err}")

    async def add_assistant(self, data: dict, _):
        new_agent = await self.create_assistant(data)

        new_tool = await self.create_tool(
            assistant=self.parent_agent.dict(),
            data={
                **data,
                "metadata": {
                    **(data.get("metadata")),
                    "agentId": new_agent.id,
                },
                "type": ToolType.AGENT.value,
            },
        )

        try:
            await api_add_agent_tool(
                agent_id=self.parent_agent.id,
                body=AgentToolRequest(
                    toolId=new_tool.id,
                ),
                api_user=self.api_user,
            )
            logger.info(f"Added assistant: {new_agent.name} - {self.parent_agent.name}")
        except Exception as err:
            logger.error(
                f"Error adding assistant: {new_agent} - {self.parent_agent} - Error: {err}"
            )

        return new_agent

    async def get_agent_tool(self, assistant: dict):
        assistant = AgentUpdateRequest.parse_obj(assistant)

        agent_tools = await prisma.agenttool.find_many(
            where={
                "agentId": self.parent_agent.id,
            },
            include={
                "tool": True,
            },
        )
        for agent_tool in agent_tools:
            if agent_tool.tool.name == assistant.name:
                return agent_tool.tool

    async def delete_assistant(self, assistant: dict):
        agent = await self.get_assistant(assistant)

        try:
            await api_delete_agent(
                agent_id=agent.id,
                api_user=self.api_user,
            )
            logger.info(f"Deleted assistant: {assistant.get('name')}")
        except Exception as err:
            logger.error(f"Error deleting assistant: {assistant} - Error: {err}")

        tool = await self.get_agent_tool(assistant)

        try:
            await api_delete_tool(
                tool_id=tool.id,
                api_user=self.api_user,
            )
            logger.info(f"Deleted tool: {assistant.get('name')}")
        except Exception as err:
            logger.error(f"Error deleting tool: {assistant} - Error: {err}")

    async def update_assistant(self, assistant: dict, data: dict):
        agent = await self.get_assistant(assistant)

        try:
            await api_update_agent(
                agent_id=agent.id,
                body=AgentUpdateRequest.parse_obj(data),
                api_user=self.api_user,
            )
            logger.info(f"Updated assistant: {assistant.get('name')}")
        except Exception as err:
            logger.error(f"Error updating assistant: {assistant} - Error: {err}")

        tool = await self.get_agent_tool(assistant)
        tool_metadata = json.loads(tool.metadata)

        try:
            await api_update_tool(
                tool_id=tool.id,
                body=ToolUpdateRequest.parse_obj(
                    {
                        **data,
                        "metadata": {
                            **(data.get("metadata")),
                            "agentId": tool_metadata.get("agentId"),
                        },
                    }
                ),
                api_user=self.api_user,
            )
            logger.info(f"Updated tool: {assistant.get('name')}")
        except Exception as err:
            logger.error(f"Error updating tool: {assistant} - Error: {err}")
