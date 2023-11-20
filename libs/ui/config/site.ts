import { GoWorkflow } from "react-icons/go"
import { PiDatabase } from "react-icons/pi"
import {
  RxAvatar,
  RxDiscordLogo,
  RxFileText,
  RxGithubLogo,
  RxGlobe,
  RxPlay,
} from "react-icons/rx"
import { TbBrain } from "react-icons/tb"

export type SiteConfig = typeof siteConfig

export const siteConfig = {
  name: "Superagent Cloud",
  description: "The agent framework for large language models",
  mainNav: [
    {
      title: "Agents",
      href: "/agents",
      icon: RxPlay,
    },
    {
      title: "workflows",
      href: "/workflows",
      icon: GoWorkflow,
    },
    {
      title: "datasources",
      href: "/datasources",
      icon: PiDatabase,
    },
    {
      title: "apis",
      href: "/apis",
      icon: RxGlobe,
    },
    {
      title: "llms",
      href: "/llms",
      icon: TbBrain,
    },
  ],
  footerNav: [
    {
      title: "Discord",
      href: "https://discord.com/invite/mhmJUTjW4b",
      icon: RxDiscordLogo,
    },
    {
      title: "Github",
      href: "https://github.com/homanp/superagent",
      icon: RxGithubLogo,
    },
    {
      title: "Documentation",
      href: "https://docs.superagent.sh",
      icon: RxFileText,
    },
    {
      title: "Settings",
      href: "/settings",
      icon: RxAvatar,
    },
  ],
  settingsNav: [
    {
      title: "User",
      href: "/settings",
    },
    {
      title: "Api keys",
      href: "/settings/api-keys",
    },
    {
      title: "Organizations",
      href: "/settings/organizations",
    },
    {
      title: "Appearance",
      href: "/settings/appearance",
    },
    {
      title: "Billing",
      href: "/settings/billing",
      disabled: true,
    },
  ],
  llms: [
    {
      id: "OPENAI",
      description:
        "Power your assistants with the latest models from OpenAI, powerful for calling external APIs and reasoning.",
      name: "OpenAI",
      logo: "/openai-logo.png",
      options: [
        {
          value: "GPT_3_5_TURBO_16K_0613",
          title: "gpt-3.5-turbo-16k-0613",
        },
        {
          value: "GPT_3_5_TURBO_0613",
          title: "gpt-3.5-turbo-0613",
        },
        {
          value: "GPT_3_5_TURBO_1106",
          title: "gpt-3.5-turbo-1106",
        },
        {
          value: "GPT_4_0613",
          title: "gpt-4-0613",
        },
        {
          value: "GPT_4_1106_PREVIEW",
          title: "gpt-4-1106-preview",
        },
      ],
    },
    {
      disabled: false,
      id: "AZURE_OPENAI",
      description:
        "Use Azure OpenAI to power your assistants with the latest OpenAI models.",
      name: "Azure OpenAI",
      logo: "/azure-logo.png",
      options: [],
    },
  ],
  datasourceTypes: [
    {
      value: "PDF",
      title: "PDF",
      type: "unstructured",
    },
    {
      value: "TXT",
      title: "TXT",
    },
    {
      value: "CSV",
      title: "CSV",
    },
    {
      value: "MARKDOWN",
      title: "Markdown",
    },
  ],
  toolTypes: [
    {
      value: "BING_SEARCH",
      title: "Bing Search",
      metadata: [
        {
          key: "bingSearchUrl",
          type: "input",
          label: "Bing Search URL",
        },
        {
          key: "bingSubscriptionKey",
          type: "input",
          label: "Bing Subscription Key",
        },
      ],
    },
    {
      value: "METAPHOR",
      title: "Metaphor Search",
      metadata: [
        {
          key: "metaphorApiKey",
          type: "input",
          label: "Metaphor API Key",
        },
      ],
    },
    {
      value: "CHATGPT_PLUGIN",
      title: "ChatGPT plugin",
      metadata: [
        {
          key: "chatgptPluginURL",
          type: "input",
          label: "Plugin manifest url",
        },
      ],
    },
    {
      value: "REPLICATE",
      title: "Replicate",
      metadata: [
        {
          key: "model",
          type: "input",
          label: "Model",
        },
        {
          key: "apiKey",
          type: "input",
          label: "Replicate API key",
        },
        {
          key: "arguments",
          type: "json",
          label: "Other arguments",
        },
      ],
    },
    {
      value: "PUBMED",
      title: "PubMed",
      metadata: [],
    },
    {
      value: "CODE_EXECUTOR",
      title: "Code interpreter (alpha)",
      metadata: [],
    },
    {
      value: "BROWSER",
      title: "Browser",
      metadata: [],
    },
    {
      value: "OPENAPI",
      title: "OpenAPI",
      metadata: [
        {
          key: "openApiUrl",
          type: "input",
          label: "OpenAPI spec url",
        },
        {
          key: "headers",
          type: "json",
          label: "Additional headers",
        },
      ],
    },
    {
      value: "GPT_VISION",
      title: "GPT Vision",
      metadata: [
        {
          key: "openaiApiKey",
          type: "input",
          label: "Your OpenAI API Key",
        },
      ],
    },
    {
      value: "TTS_1",
      title: "Text-To-Speech (TTS1)",
      metadata: [
        {
          key: "openaiApiKey",
          type: "input",
          label: "Your OpenAI API Key",
        },
      ],
    },
    {
      value: "WOLFRAM_ALPHA",
      title: "Wolfram Alpha",
      metadata: [
        {
          key: "appId",
          type: "input",
          label: "Wolfram App ID",
        },
      ],
    },
    {
      value: "ZAPIER_NLA",
      title: "Zapier Natural Language",
      metadata: [
        {
          key: "zapierNlaApiKey",
          type: "input",
          label: "Zapier NLA API key",
        },
        {
          key: "openaiApiKey",
          type: "input",
          label: "Your OpenAI API key",
        },
      ],
    },
    {
      value: "AGENT",
      title: "Agent",
      metadata: [
        {
          key: "agentId",
          type: "input",
          label: "Superagent Agent ID",
        },
        {
          key: "apiKey",
          type: "input",
          label: "Superagent API key",
        },
      ],
    },
  ],
}
