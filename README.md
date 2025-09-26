# Welcome to Vista API MCP Server

This repository contains documentation about a Model Context Protocol (MCP) server that provides secure access to VA's VistA electronic health record (EHR) system, enabling AI applications to retrieve and summarize patient medical records for clinical staff.

## Overview

The Vista API MCP Server enables Large Language Models (LLMs) to securely access VistA by acting as a bridge that safely connects LLMs to patient medical records and clinical documentation. The server can be consumed by multiple AI applications, like [AI Assist](https://github.com/department-of-veterans-affairs/ai-assist-example), to perform summarization or other LLM-enabled tasks.

### What is an MCP server?

Model Context Protocol (MCP) servers follow a standardized protocol to expose resources, tools, and prompts to AI applications. They act as bridges that allow AI applications to access external capabilities without each application needing to implement custom integrations.

In this case, our MCP server converts VistA's legacy data formats for contemporary AI applications. VistA contains large amounts of patient data that is difficult to access programmatically. The MCP server allows authorized AI applications to access this rich clinical data without requiring each application to understand VistA's specific database structure or APIs.

Healthcare data is notoriously complex—lab results, medication histories, diagnostic imaging, and clinical notes all have different formats. The MCP server standardizes how this data is presented to AI applications, making it easier to build clinical tools.

### How is an MCP server different from an LLM?

The MCP server acts as a secure data gateway that retrieves specific patient information from VistA and formats it for an LLM. The LLM can then process and generate human-like text responses based on prompts. The distinction is that the LLM does not directly access VistA or understand medical record formats, the MCP server is the bridge.

### What’s the value of this MCP server?

Without an MCP server, teams would need to build VistA integration directly into each AI application, leading to technical debt, security risks, and development inefficiencies.

Whereas, any application that supports Model Context Protocol can consume this server. Think of it as a reusable data service that multiple products can leverage while maintaining strict security boundaries. For example, a medication management tool and AI Assist could both use the same MCP server to access patient data without each building their own VistA integration. This approach is faster, more secure, and creates reusable infrastructure that accelerates future VA AI initiatives.

## Roadmap

Our roadmap provides an overview of how we plan to build this MCP server.

![roadmap](docs/roadmap-september-2025.png)

Review our roadmap in [VA Mural](https://app.mural.co/t/departmentofveteransaffairs9999/m/departmentofveteransaffairs9999/1750882921059/550b745268addb245a7f73287ec7645b6fa0d2c7?sender=u65f0a75fc7c68f2a5a2a9545).

## Get started

- [Development guide](docs/DEVELOPMENT.md) - Setup instructions and development workflows
- [Deployment guide](docs/DEPLOYMENT.md) - Production deployment instructions
- [Test data guide](docs/TEST_DATA.md) - Test patient IDs and sample data
- [Logging guide](docs/LOGGING.md) - Logging configuration and best practices

## Connect with us

Reach out on Office of CTO Slack: [#va-ai-chat-public](https://dsva.slack.com/archives/C099YJ3ESJ0)
