import requests
from langchain_community.tools import BaseTool
from pydantic import BaseModel, Field

class OlostepBrowserArgs(BaseModel):
    url: str = Field(..., description="A valid url including protocol to analyze")
    formatType: str = Field("markdown", description="The formatType of the content that will be returned. Can be 'html' or 'markdown'")
    waitBeforeScraping: int = Field(1, description="Seconds to wait before scraping after the page is loaded")
    removeImages: bool = Field(True, description="Remove images from the page before scraping")
    htmlTransformer: str = Field("none", description="The htmlTransformer to use. If you pass 'postlightParser', Postlight's Mercury Parser library is used to remove ads and other unwanted content from the scraped page.")

class OlostepBrowser(BaseTool):
    args_schema = OlostepBrowserArgs

    def __init__(self):
        self.api_token = self.metadata["olostepApiToken"]

    def make_request(self, url, params=None):
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e.response.text}")
            return None

    def start_agent(self, start_url, formatType="markdown", waitBeforeScraping=1, removeImages=True, htmlTransformer="none"):
        endpoint = "https://agent.olostep.com/olostep-p2p-incomingAPI"
        query_params = {
            "token": self.api_token,
            "url": start_url,
            "timeout": 35,
            "waitBeforeScraping": waitBeforeScraping,
            "saveHtml": True,
            "saveMarkdown": True,
            "removeCSSselectors": "default",
            "htmlTransformer": htmlTransformer,
            "removeImages": removeImages,
            "expandMarkdown": formatType == "markdown",
            "expandHtml": formatType == "html",
        }
        json_response = self.make_request(endpoint, params=query_params)
        if json_response:
            if formatType == "markdown":
                return json_response["markdown_content"]
            else:
                return json_response["html_content"]

    async def arun(self, args: OlostepBrowserArgs) -> dict:
        url = args.url

        if not url.startswith(("http://", "https://")):
            url = "http://" + url

        content = self.start_agent(
            url,
            args.formatType,
            args.waitBeforeScraping,
            args.removeImages,
            args.htmlTransformer
        )

        return {"type": "function_call", "content": content}