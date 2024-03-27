import logging

from app.api.workflow_configs.api.api_manager import ApiManager
from app.api.workflow_configs.saml_schema import SAML_OSS_LLM_PROVIDERS
from app.utils.helpers import (
    get_first_non_null_key,
    get_mimetype_from_url,
    get_superrag_compatible_credentials,
    remove_key_if_present,
    rename_and_remove_keys,
)
from app.utils.llm import LLM_REVERSE_MAPPING, get_llm_provider
from app.vectorstores.base import REVERSE_VECTOR_DB_MAPPING
from prisma.enums import AgentType, ToolType

logger = logging.getLogger(__name__)


DEFAULT_ENCODER_OPTIONS = {
    "type": "cohere",
    "name": "embed-multilingual-light-v3.0",
    "dimensions": 384,
}


SUPERRAG_MIME_TYPE_TO_EXTENSION = {
    "text/plain": "TXT",
    "text/markdown": "MD",
    "application/pdf": "PDF",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "DOCX",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "XLSX",
    "text/csv": "CSV",
}


class MissingVectorDatabaseProvider(Exception):
    pass


class UnkownFileType(Exception):
    pass


# Source https://stackoverflow.com/questions/33797126/proper-way-to-remove-keys-in-dictionary-with-none-values-in-python
def delete_none_values(_dict):
    """Delete None values recursively from all of the dictionaries"""
    for key, value in list(_dict.items()):
        if isinstance(value, dict):
            delete_none_values(value)
        elif value is None:
            del _dict[key]
        elif isinstance(value, list):
            for v_i in value:
                if isinstance(v_i, dict):
                    delete_none_values(v_i)

    return _dict


class DataTransformer:
    def __init__(
        self,
        api_user,
        api_manager: ApiManager,
        assistant,
        assistant_type,
        tools,
        superrags,
    ):
        self.api_user = api_user
        self.api_manager = api_manager
        self.assistant = assistant
        self.assistant_type = assistant_type
        self.tools = tools
        self.superrags = superrags

    async def transform(
        self,
    ):
        self.transform_tools()
        await self.transform_superrags()

        self.transform_assistant()

        delete_none_values(self.assistant)

    def transform_assistant(self):
        rename_and_remove_keys(
            self.assistant, {"llm": "llmModel", "intro": "initialMessage"}
        )

        if self.assistant_type:
            if self.assistant_type.upper() in SAML_OSS_LLM_PROVIDERS:
                self.assistant_type = AgentType.LLM.value

            self.assistant["type"] = self.assistant_type.upper()

        llm_model = self.assistant.get("llmModel")

        if self.assistant.get("type") == AgentType.LLM.value:
            self.assistant["metadata"] = {
                "model": llm_model,
                **self.assistant.get("metadata", {}),
            }

            provider = get_llm_provider(llm_model)
            if provider:
                self.assistant["llmProvider"] = provider

        if self.assistant.get("type") == AgentType.LLM.value:
            remove_key_if_present(self.assistant, "llmModel")
        else:
            self.assistant["llmModel"] = LLM_REVERSE_MAPPING.get(
                llm_model, llm_model)

        self.assistant["metadata"] = {
            **(self.assistant.get("params") or {}),
            **(self.assistant.get("metadata") or {}),
        }

    def transform_tools(self):
        for tool_obj in self.tools:
            tool_type = get_first_non_null_key(tool_obj)
            tool = tool_obj.get(tool_type)

            rename_and_remove_keys(
                tool, {"use_for": "description",
                       "return_direct": "returnDirect"}
            )

            if tool_type:
                tool["type"] = tool_type.upper()

            if tool.get("type") == ToolType.FUNCTION.value:
                tool["metadata"] = {
                    "functionName": tool.get("name"),
                    **tool.get("metadata", {}),
                }

    async def transform_superrags(self):
        for superrag_obj in self.superrags:
            node_type = get_first_non_null_key(superrag_obj)
            datasource = superrag_obj.get(node_type, {})

            rename_and_remove_keys(datasource, {"use_for": "description"})

            await self._set_superrag_files(datasource)
            await self._set_database_provider(datasource)
            encoder = datasource.get("encoder") or DEFAULT_ENCODER_OPTIONS
            rename_and_remove_keys(encoder, {"type": "provider"})
            rename_and_remove_keys(encoder, {"name": "model_name"})

            datasource["document_processor"] = {
                "encoder": encoder,
                "unstructured": {
                    "hi_res_model_name": "detectron2_onnx",
                    "partition_strategy": "auto",
                    "process_tables": False,
                },
                "splitter": {
                    "max_tokens": 400,
                    "min_tokens": 30,
                    "name": "by_title",
                    "prefix_summary": True,
                    "prefix_title": True,
                    "rolling_window_size": 1,
                },
            }

    async def _set_database_provider(self, datasource: dict):
        database_provider = datasource.get("database_provider")
        if database_provider:
            database = await self.api_manager.get_vector_database_by_provider(
                database_provider
            )
        else:
            database = await self.api_manager.get_vector_database_by_user_id()
            logger.info(
                f"Database provider is not set, using default provider - {database}"
            )

        # this is for superrag
        if database:
            database_provider = REVERSE_VECTOR_DB_MAPPING.get(
                database.provider)
            credentials = get_superrag_compatible_credentials(database.options)
            datasource["vector_database"] = {
                "type": database_provider,
                "config": credentials,
            }
        else:
            raise MissingVectorDatabaseProvider(
                "Vector database provider not found."
                "Please configure it by going to the integrations page"
            )
        remove_key_if_present(datasource, "database_provider")

    async def _set_superrag_files(self, datasource: dict):
        urls = datasource.get("urls") or []
        files = []

        for url in urls:
            file_type = self._get_file_type(url)
            files.append(
                {
                    "type": file_type,
                    "url": url,
                }
            )

        datasource["files"] = files
        remove_key_if_present(datasource, "urls")

    def _get_file_type(self, url: str):
        try:
            file_type = SUPERRAG_MIME_TYPE_TO_EXTENSION[get_mimetype_from_url(
                url)]
        except KeyError:
            supported_file_types = ", ".join(
                value for value in SUPERRAG_MIME_TYPE_TO_EXTENSION.values()
            )
            raise UnkownFileType(
                f"Unknown file type for URL {url}"
                f"Supported file types are: {supported_file_types}"
            )

        return file_type
