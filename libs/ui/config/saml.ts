import { JSONSchema4 } from "json-schema"

export const initialSamlValue = `# 👋 Welcome! Start creating your workflows using example yaml below.
# More info in our docs: https://docs.superagent.sh/overview/getting-started/super-agent-markup-language

workflows:
  - superagent:
      llm: gpt-4-1106-preview
      name: Earnings assistant
      intro: 👋 Hi there! How can I help you?
      prompt: Use the earnings report to answer any questions
      data:
        urls:
          - https://s2.q4cdn.com/299287126/files/doc_financials/2023/q3/AMZN-Q3-2023-Earnings-Release.pdf
        use_for: Answering questions about earning report
`

export const exampleConfigs = {
  browserYaml: `# 🤖 This agent workflow has access to the browser tool and can access the internet in real-time.
# More info in our docs: https://docs.superagent.sh/overview/getting-started/super-agent-markup-language

workflows:
  - superagent: 
      name: Browser assistant
      llm: gpt-3.5-turbo-16k-0613
      prompt: Use the browser to answer all questions
      intro: 👋 Hi there! How can I help you?
      tools:
        - browser:
            name: browser tool
            use_for: searching the internet`,
  ragYaml: `# 🤖 This agent workflow has access to external data.
# More info in our docs: https://docs.superagent.sh/overview/getting-started/super-agent-markup-language
  
workflows:
  - superagent: 
      name: Titanic assistant
      llm: gpt-3.5-turbo-16k-0613
      prompt: Use the excel file to answer all questions.
      intro: 👋 Hi there! How can I help you?
      data:
        urls:
          - https://raw.githubusercontent.com/datasciencedojo/datasets/master/titanic.csv
        use_for: Answering questions about the titanic`,
  multiAssistantYaml: `# 🤖 This is an example of a multi-agent workflow.
  # More info in our docs: https://docs.superagent.sh/overview/getting-started/super-agent-markup-language
  
workflows:
  - superagent: 
      name: Code writer
      llm: gpt-4-1106-preview
      prompt: |- 
        You are an expert coder, write code based on the users input.
        Only return the filename and code.
      intro: 👋 Hi there! What code do you want me to write?
  - superagent:
      name: Code reviewer
      llm: gpt-4-1106-preview
      prompt: |- 
        You are an code reviewer. Review the code and write a 
        Github comment.`,
}
// TODO: get this from the backend after migrating to pydantic version 2
export const yamlJsonSchema = {
  $schema: "http://json-schema.org/draft-07/schema#",

  type: "object",
  properties: {
    workflows: {
      type: "array",
      items: {
        type: "object",
        properties: {
          superagent: {
            $ref: "#/definitions/agent",
          },
          openai_assistant: {
            $ref: "#/definitions/agent",
          },
          llm: {
            $ref: "#/definitions/assistant",
          },
        },
      },
    },
  },
  definitions: {
    assistant: {
      type: "object",
      properties: {
        name: { type: "string" },
        llm: { type: "string" },
        prompt: { type: "string" },
        intro: { type: "string" },
      },
    },
    agent: {
      allOf: [{ $ref: "#/definitions/assistant" }],
      properties: {
        tools: {
          $ref: "#/definitions/tools",
        },
        data: {
          $ref: "#/definitions/data",
        },
        superrag: {
          $ref: "#/definitions/superrag",
        },
      },
    },
    superrag: {
      type: "array",
      items: {
        type: "object",
        properties: {
          index: {
            type: "object",
            properties: {
              name: { type: "string" },
              urls: {
                type: "array",
                items: { type: "string" },
              },
              use_for: { type: "string" },
            },
          },
        },
      },
    },
    tools: {
      type: "array",
      items: {
        type: "object",
        properties: {
          browser: {
            $ref: "#/definitions/tool",
          },
          code_executor: {
            $ref: "#/definitions/tool",
          },
          hand_off: {
            $ref: "#/definitions/tool",
          },
          http: {
            $ref: "#/definitions/tool",
          },
          bing_search: {
            $ref: "#/definitions/tool",
          },
          replicate: {
            $ref: "#/definitions/tool",
          },
          algolia: {
            $ref: "#/definitions/tool",
          },
          metaphor: {
            $ref: "#/definitions/tool",
          },
          function: {
            $ref: "#/definitions/tool",
          },
          // for openai assistant
          code_interpreter: {
            $ref: "#/definitions/tool",
          },
          // for openai assistant
          retrieval: {
            $ref: "#/definitions/tool",
          },
        },
      },
    },
    data: {
      type: "object",
      properties: {
        urls: {
          type: "array",
          items: { type: "string" },
        },
        use_for: { type: "string" },
      },
    },

    tool: {
      type: "object",
      properties: {
        name: { type: "string" },
        use_for: { type: "string" },
        metadata: {
          type: "object",
          properties: {
            headers: {
              type: "object",
              additionalProperties: { type: "string" },
            },
            url: { type: "string" },
            method: { type: "string" },
            body: { type: "object" },
          },
        },
      },
    },
  },
  required: ["workflows"],
} satisfies JSONSchema4
