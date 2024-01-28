import json
import logging
from itertools import zip_longest
from typing import Any, Dict, List, Optional

import segment.analytics as analytics
import yaml
from decouple import config
from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel

from app.api.agents import (
    add_datasource as api_add_agent_datasource,
)
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
from app.api.datasources import (
    create as api_create_datasource,
)
from app.api.datasources import (
    delete as api_delete_datasource,
)
from app.api.tools import (
    create as api_create_tool,
)
from app.api.tools import (
    delete as api_delete_tool,
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
    Datasource as DatasourceRequest,
)
from app.models.request import (
    Tool as ToolRequest,
)
from app.models.request import (
    WorkflowConfig as WorkflowConfigRequest,
)
from app.utils.api import get_current_api_user, handle_exception
from app.utils.helpers import (
    MIME_TYPE_TO_EXTENSION,
    compare_dicts,
    get_mimetype_from_url,
    remove_key_if_present,
    rename_and_remove_key,
)
from app.utils.llm import LLM_REVERSE_MAPPING
from app.utils.prisma import prisma

SEGMENT_WRITE_KEY = config("SEGMENT_WRITE_KEY", None)

router = APIRouter()
logger = logging.getLogger(__name__)
analytics.write_key = SEGMENT_WRITE_KEY


class WorkflowDatasource(BaseModel):
    use_for: Optional[str]  # an alias for description
    urls: Optional[List[str]]


class WorkflowTool(BaseModel):
    name: str
    use_for: Optional[str]  # an alias for description
    metadata: Optional[Dict[Any, Any]]


class WorkflowAssistant(BaseModel):
    name: str
    llm: str  # an alias for llmModel
    prompt: str
    intro: Optional[str]  # an alias for initialMessage

    tools: Optional[List[Dict[str, WorkflowTool]]]
    data: Optional[WorkflowDatasource]


class WorkflowConfig(BaseModel):
    workflows: List[Dict[str, WorkflowAssistant]]


@router.post("/workflow-config")
async def create_workflow_config(
    body: WorkflowConfigRequest,
    api_user=Depends(get_current_api_user),
):
    try:
        workflow_config = await prisma.workflowconfig.create(
            data={
                **body.dict(),
                "apiUserId": api_user.id,
            }
        )

        return {"workflow_config": workflow_config}
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Error creating workflow config: {str(e)}"
        )


class WorkflowConfigHandler:
    def __init__(self, workflow_config_id: str, api_user):
        self.workflow_config_id = workflow_config_id
        self.api_user = api_user

    async def delete_tool(self, tool_name: str, assistant_name: str):
        workflow_config_agent = await prisma.agent.find_first(
            where={
                "name": assistant_name,
                "workflowConfigId": self.workflow_config_id,
                "apiUserId": self.api_user.id,
            }
        )

        tool = await prisma.tool.find_first(
            where={
                "name": tool_name,
                "workflowConfigId": self.workflow_config_id,
                "workflowConfigAgentId": workflow_config_agent.id,
                "apiUserId": self.api_user.id,
            }
        )

        await api_delete_tool(
            tool_id=tool.id,
            api_user=self.api_user,
        )

        logger.info(f"Deleted tool: ${tool_name} - ${assistant_name}")

    async def add_tool(self, assistant_name: str, type: str, data: Dict[str, str]):
        agent = await prisma.agent.find_first(
            where={
                "name": assistant_name,
                "workflowConfigId": self.workflow_config_id,
                "apiUserId": self.api_user.id,
            }
        )

        rename_and_remove_key(data, "use_for", "description")
        data["type"] = type

        data["workflowConfigId"] = self.workflow_config_id
        data["workflowConfigAgentId"] = agent.id

        tool_res = await api_create_tool(
            body=ToolRequest(**data),
            api_user=self.api_user,
        )

        new_tool = tool_res.get("data", {})

        await self._add_agent_tool(
            assistant_name=assistant_name,
            tool_id=new_tool.id,
        )

        logger.info(f"Added tool: ${new_tool.name} - ${assistant_name}")

    async def add_datasource(self, assistant_name: str, data: Dict[str, str]):
        agent = await prisma.agent.find_first(
            where={
                "name": assistant_name,
                "workflowConfigId": self.workflow_config_id,
                "apiUserId": self.api_user.id,
            }
        )
        datasourceRes = await api_create_datasource(
            body=DatasourceRequest(
                **{
                    **data,
                    "workflowConfigId": self.workflow_config_id,
                    "workflowConfigAgentId": agent.id,
                }
            ),
            api_user=self.api_user,
        )

        new_datasource = datasourceRes.get("data", {})

        await self._add_agent_datasource(
            agent_id=agent.id,
            datasource_id=new_datasource.id,
        )

        logger.info(f"Added datasource: {data}")

    async def delete_datasource(self, assistant_name: str, datasource_name: str):
        agent = await prisma.agent.find_first(
            where={
                "name": assistant_name,
                "workflowConfigId": self.workflow_config_id,
                "apiUserId": self.api_user.id,
            }
        )

        datasource = await prisma.datasource.find_first(
            where={
                "name": datasource_name,
                "workflowConfigId": self.workflow_config_id,
                "workflowConfigAgentId": agent.id,
                "apiUserId": self.api_user.id,
            }
        )

        await api_delete_datasource(
            datasource_id=datasource.id,
            api_user=self.api_user,
        )

        logger.info(f"Deleted datasource: {datasource_name} - {assistant_name}")

    async def add_assistant(self, data: Dict[str, str]):
        new_agent = data

        rename_and_remove_key(new_agent, "llm", "llmModel")
        rename_and_remove_key(new_agent, "intro", "initialMessage")

        new_agent["llmModel"] = LLM_REVERSE_MAPPING[new_agent["llmModel"]]

        await api_create_agent(
            body=AgentRequest(
                **{
                    **new_agent,
                    "workflowConfigId": self.workflow_config_id,
                }
            ),
            api_user=self.api_user,
        )
        logger.info(f"Added agent: {new_agent}")

    async def delete_assistant(self, assistant_name: str):
        agent = await prisma.agent.find_first(
            where={
                "name": assistant_name,
                "workflowConfigId": self.workflow_config_id,
                "apiUserId": self.api_user.id,
            }
        )

        await api_delete_agent(
            agent_id=agent.id,
            api_user=self.api_user,
        )
        logger.info(f"Deleted agent: {assistant_name}")

    async def update_assistant(self, assistant_name: str, data: Dict[str, str]):
        agent = await prisma.agent.find_first(
            where={
                "name": assistant_name,
                "workflowConfigId": self.workflow_config_id,
                "apiUserId": self.api_user.id,
            }
        )

        await api_update_agent(
            agent_id=agent.id,
            body=AgentUpdateRequest(**data),
            api_user=self.api_user,
        )
        logger.info(f"Updated agent: {assistant_name} - {data}")

    async def update_tool(
        self, assistant_name: str, tool_name: str, data: Dict[str, str]
    ):
        agent = await prisma.agent.find_first(
            where={
                "name": assistant_name,
                "workflowConfigId": self.workflow_config_id,
                "apiUserId": self.api_user.id,
            }
        )

        tool = await prisma.tool.find_first(
            where={
                "name": tool_name,
                "workflowConfigId": self.workflow_config_id,
                "workflowConfigAgentId": agent.id,
                "apiUserId": self.api_user.id,
            }
        )

        await prisma.tool.update(
            where={
                "id": tool.id,
            },
            data=data,
        )

        logger.info(f"Updated tool: {tool_name} - {assistant_name}")

    async def _add_agent_tool(self, assistant_name: str, tool_id: str):
        agent = await prisma.agent.find_first(
            where={
                "name": assistant_name,
                "workflowConfigId": self.workflow_config_id,
                "apiUserId": self.api_user.id,
            }
        )

        await api_add_agent_tool(
            agent_id=agent.id,
            body=AgentToolRequest(
                toolId=tool_id,
            ),
            api_user=self.api_user,
        )
        logger.info(f"Added agent tool: {tool_id} - {assistant_name}")

    async def _add_agent_datasource(self, agent_id: str, datasource_id: str):
        await api_add_agent_datasource(
            agent_id=agent_id,
            body={
                "datasourceId": datasource_id,
            },
            api_user=self.api_user,
        )
        logger.info(f"Added agent datasource: {agent_id} - {datasource_id}")

    async def process_tools(self, old_tools, new_tools, assistant_name):
        # Process individual tools
        tools_length = max(len(old_tools), len(new_tools))

        for tool_step in range(tools_length):
            old_tool_obj = old_tools[tool_step] if tool_step < len(old_tools) else {}
            new_tool_obj = new_tools[tool_step] if tool_step < len(new_tools) else {}

            old_tool_type: str = next(iter(old_tool_obj)) if old_tool_obj else None
            new_tool_type: str = next(iter(new_tool_obj)) if new_tool_obj else None

            old_tool = old_tool_obj.get(old_tool_type, {})
            new_tool = new_tool_obj.get(new_tool_type, {})

            if old_tool_type and new_tool_type:
                if old_tool_type != new_tool_type:
                    await self.delete_tool(
                        tool_name=old_tool.get("name"),
                        assistant_name=assistant_name,
                    )
                    await self.add_tool(
                        assistant_name=assistant_name,
                        type=new_tool_type.upper(),
                        data=new_tool,
                    )
                else:
                    changes = compare_dicts(old_tool, new_tool)
                    if changes:
                        await self.update_tool(
                            assistant_name=assistant_name,
                            tool_name=old_tool["name"],
                            data=changes,
                        )
            elif old_tool_type and not new_tool_type:
                await self.delete_tool(
                    tool_name=old_tool.get("name"),
                    assistant_name=assistant_name,
                )

            elif new_tool_type and not old_tool_type:
                await self.add_tool(
                    assistant_name=assistant_name,
                    type=new_tool_type.upper(),
                    data=new_tool,
                )

    async def process_data(self, old_data, new_data, assistant_name):
        old_urls = old_data.get("urls") or []
        new_urls = new_data.get("urls") or []

        # Process data URLs changes
        for url in set(old_urls) | set(new_urls):
            if url in old_urls and url not in new_urls:
                await self.delete_datasource(
                    assistant_name,
                    datasource_name=url,
                )

            elif url in new_urls and url not in old_urls:
                type = get_mimetype_from_url(url)

                if type in MIME_TYPE_TO_EXTENSION:
                    await self.add_datasource(
                        assistant_name=assistant_name,
                        data={
                            # TODO: this will be changed once we implement superrag
                            "name": url,
                            "description": new_data.get("use_for"),
                            "url": url,
                            "type": MIME_TYPE_TO_EXTENSION[type],
                        },
                    )

    async def process_assistant(self, old_assistant_obj, new_assistant_obj):
        old_type = next(iter(old_assistant_obj)) if old_assistant_obj else None
        new_type = next(iter(new_assistant_obj)) if new_assistant_obj else None

        old_assistant = old_assistant_obj.get(old_type, {})
        new_assistant = new_assistant_obj.get(new_type, {})

        old_data = old_assistant.get("data") or {}
        new_data = new_assistant.get("data") or {}

        old_tools = old_assistant.get("tools") or []
        new_tools = new_assistant.get("tools") or []

        # Remove 'data' and 'tools' keys from assistant objects
        remove_key_if_present(old_assistant, "data")
        remove_key_if_present(old_assistant, "tools")
        remove_key_if_present(new_assistant, "data")
        remove_key_if_present(new_assistant, "tools")

        if old_type and new_type:
            if old_type != new_type:
                await self.process_tools(
                    old_tools, new_tools, old_assistant.get("name")
                )
                await self.delete_assistant(
                    assistant_name=old_assistant["name"],
                )
                await self.add_assistant(data=new_assistant)
                await self.process_tools(
                    old_tools, new_tools, new_assistant.get("name")
                )
                await self.process_data(
                    old_data,
                    new_data,
                    new_assistant.get("name"),
                )

            else:
                changes = compare_dicts(old_assistant, new_assistant)
                await self.process_tools(
                    old_tools, new_tools, old_assistant.get("name")
                )
                await self.process_data(
                    old_data,
                    new_data,
                    old_assistant.get("name"),
                )
                if changes:
                    await self.update_assistant(
                        assistant_name=old_assistant["name"], data=changes
                    )
        elif old_type and not new_type:
            await self.process_tools(old_tools, new_tools, old_assistant.get("name"))
            await self.process_data(
                old_data,
                new_data,
                old_assistant.get("name"),
            )

            await self.delete_assistant(
                assistant_name=old_assistant["name"],
            )
        elif new_type and not old_type:
            await self.add_assistant(
                data=new_assistant,
            )
            await self.process_tools(old_tools, new_tools, new_assistant.get("name"))
            await self.process_data(
                old_data,
                new_data,
                new_assistant.get("name"),
            )

    async def handle_changes(self, old_config, new_config):
        old_assistants = old_config.get("workflows", [])
        new_assistants = new_config.get("workflows", [])

        for old_assistant, new_assistant in zip_longest(
            old_assistants, new_assistants, fillvalue={}
        ):
            await self.process_assistant(old_assistant, new_assistant)


@router.post("/workflow-config/{workflow_config_id}/")
async def parse_yaml(
    workflow_config_id: str,
    yaml_content: str = Body(..., media_type="application/x-yaml"),
    api_user=Depends(get_current_api_user),
):
    try:
        workflow_config = await prisma.workflowconfig.find_unique(
            where={"id": workflow_config_id}
        )

        try:
            parsed_yaml = yaml.safe_load(yaml_content)
            # validating the parsed yaml
            new_config = WorkflowConfig(**parsed_yaml).dict()
        except yaml.YAMLError as e:
            logger.error("Invalid YAML: ", e)
            raise HTTPException(status_code=400, detail=f"Error parsing YAML: {str(e)}")

        new_config_str = json.dumps(new_config)

        old_workflow_config_history = None
        if workflow_config.latestWorkflowConfigHistoryId:
            old_workflow_config_history = await prisma.workflowconfighistory.find_first(
                where={
                    "workflowConfigId": workflow_config_id,
                    "id": workflow_config.latestWorkflowConfigHistoryId,
                }
            )

        new_config = json.loads(new_config_str)
        old_config = (
            {}
            if not old_workflow_config_history
            else old_workflow_config_history.configFile
        )

        workflow_config_handler = WorkflowConfigHandler(
            workflow_config_id=workflow_config_id,
            api_user=api_user,
        )
        await workflow_config_handler.handle_changes(old_config, new_config)

        new_workflow_config_history = await prisma.workflowconfighistory.create(
            data={
                "configFile": new_config_str,
                "workflowConfigId": workflow_config_id,
            }
        )

        await prisma.workflowconfig.update(
            where={"id": workflow_config_id},
            data={
                "latestWorkflowConfigHistoryId": new_workflow_config_history.id,
            },
        )

        return {"success": True}
    except Exception as e:
        handle_exception(e)