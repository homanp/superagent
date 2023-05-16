# SuperAgent 🥷

<p>
<img alt="GitHub Contributors" src="https://img.shields.io/github/contributors/homanp/superagent" />
<img alt="GitHub Last Commit" src="https://img.shields.io/github/last-commit/homanp/superagent" />
<img alt="" src="https://img.shields.io/github/repo-size/homanp/superagent" />
<img alt="GitHub Issues" src="https://img.shields.io/github/issues/homanp/superagent" />
<img alt="GitHub Pull Requests" src="https://img.shields.io/github/issues-pr/homanp/superagent" />
<img alt="Github License" src="https://img.shields.io/badge/License-MIT-yellow.svg" />
</p>

SuperAgent is a powerful tool that simplifies the configuration and deployment of LLM (Language Model) Agents to production. It provides a range of features and functionalities to make it easier for developers to work with LLMs and create conversational agents.

## Roadmap

Here's an overview of the roadmap for SuperAgent:

- [x] Bring your own DB: SuperAgent allows you to use your own database to store agent-related data.
- [x] Authentication: Authentication mechanisms are implemented to secure the SuperAgent application.
- [x] ChatGPT clone: SuperAgent includes a clone of ChatGPT, a powerful conversational AI model.
- [x] Built-in memory: SuperAgent has a built-in memory to store context and information during conversations.
- [x] REST API: SuperAgent provides a REST API to interact with the agents and perform various operations.
- [x] Support for multiple LLMs: SuperAgent supports multiple Language Models, allowing you to choose the most suitable one for your needs.
- [x] Streaming support: SuperAgent supports streaming conversations for real-time communication.
- [x] Built-in vectorstore: SuperAgent includes a built-in vector store for efficient vector-based search and retrieval.
- [x] Built-in document retrieval: SuperAgent offers document retrieval capabilities for finding relevant information.
- [x] Q&A Agents: SuperAgent supports the creation of Q&A agents for answering specific questions.
- [ ] Tools: SuperAgent includes various tools to enhance agent development and management.
- [ ] ReAct Agents with Tools: SuperAgent enables the creation of reactive agents with the help of provided tools.
- [ ] Plan-solve Agents with Tools: SuperAgent supports the creation of plan-solve agents with the help of provided tools.
- [ ] Prompt management: SuperAgent includes features for managing and configuring prompts for the agents.
- [ ] Bring your own LLM: SuperAgent allows you to bring your own Language Model to use with the platform.
- [ ] Usage quotas and tracking: SuperAgent provides usage quotas and tracking mechanisms for better resource management.
- [ ] Python SDK: SuperAgent offers a Python Software Development Kit (SDK) for easier integration and development.
- [ ] Typescript SDK: SuperAgent provides a Typescript SDK for developers who prefer using Typescript.
- [ ] SuperAgent CLI: SuperAgent includes a command-line interface (CLI) for managing and deploying agents.
- [ ] One-click deploy (GCP, Amazon, DigitalOcean): SuperAgent aims to provide a one-click deploy feature for popular cloud platforms like GCP, Amazon, and DigitalOcean.

## Stack

SuperAgent is built on the following technologies and frameworks:

- [FastAPI](https://fastapi.tiangolo.com/): A modern, fast (high-performance) web framework for building APIs with Python.
- [Supabase](https://supabase.com/): An open-source alternative to Firebase that provides a suite of tools for building scalable applications.
- [LangChain](https://python.langchain.com/en/latest/): A Python library for natural language processing and understanding.
- [Prisma](https://www.prisma.io/): A modern database toolkit that simplifies database access and management.
- [Pinecone](https://www.pinecone.io/): A vector database that enables fast similarity search and retrieval.

## Getting Started

To get started with SuperAgent, follow these steps:

1. Clone the SuperAgent repository into a public GitHub repository or fork it from [https://github.com/homanp/superagent/fork](https://github.com/homanp/superagent/fork). If you plan to distribute the code, keep the source code public.

   ```sh


   git clone https://github.com/homanp/superagent.git
   ```

2. Create and activate a virtual environment.

   ```sh
   virtualenv venv
   source venv/bin/activate
   ```

3. Install dependencies using `Poetry`.

   ```sh
   poetry install
   ```

4. Set up your `.env` file.

   ```sh 
   cp .env.example .env
   ```
   - Configure the environment variables according to your requirements.

5. Run database migrations.
 
   ```sh
   poetry run prisma migrate dev
   ```

6. Run the SuperAgent project.

   ```sh
   uvicorn app.main:app --reload
   ```

## Deployment

You can deploy SuperAgent using the "Deploy to DO" button, which will take you to the DigitalOcean App platform for easy deployment. Click on the button below to deploy:

[![Deploy to DO](https://www.deploytodo.com/do-btn-blue.svg)](https://cloud.digitalocean.com/apps/new?repo=https://github.com/homanp/superagent/tree/main)

## Contributions

SuperAgent is an open-source project, and contributions are welcome. If you would like to contribute, you can create new features, fix bugs, or improve the infrastructure. Please refer to the [CONTRIBUTING.md](https://github.com/homanp/superagent/blob/main/.github/CONTRIBUTING.md) file in the repository for more information on how to contribute.

We appreciate your contributions and aim to make it easy for anyone to create and run LLM Agents in production using SuperAgent.
