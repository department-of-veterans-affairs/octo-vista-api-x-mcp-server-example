# Vista API X MCP Server Documentation

This directory contains comprehensive documentation for the Vista API X MCP Server project.

## Documentation Structure

### Setup & Configuration
- [SETUP.md](SETUP.md) - Initial project setup and requirements
- [CLIENT_SETUP.md](CLIENT_SETUP.md) - MCP client configuration (Claude Desktop, Cursor, etc.)
- [DEVELOPMENT.md](DEVELOPMENT.md) - Development workflow and best practices

### Architecture & Design
- [ARCHITECTURE.md](ARCHITECTURE.md) - System design and component overview
- [TRANSPORTS.md](TRANSPORTS.md) - MCP transport modes (stdio vs SSE)
- [TOOLS.md](TOOLS.md) - Available MCP tools and their usage
- [PROMPTS.md](PROMPTS.md) - Built-in prompts for healthcare workflows

### Deployment & Operations
- [DEPLOYMENT.md](DEPLOYMENT.md) - Production deployment guide (AWS, Azure)
- [TESTING.md](TESTING.md) - Testing guide with sample data

## Quick Start

1. **Setup**: Follow [SETUP.md](SETUP.md) to install dependencies
2. **Development**: Use `mise run dev-with-mock` to start with mock server
3. **Client**: Configure your MCP client using [CLIENT_SETUP.md](CLIENT_SETUP.md)
4. **Deploy**: See [DEPLOYMENT.md](DEPLOYMENT.md) for production deployment

## Development Commands

```bash
# Start with mock server
mise run dev-with-mock

# Start SSE mode with mock
mise run dev-sse-with-mock

# Run linting
mise lint

# Run tests
mise test
```

## CI/CD

- **Branch Protection**: `main` and `master` branches are protected
- **Automated Tests**: Run on all PRs via GitHub Actions
- **Linting**: Black formatting and Ruff checks enforced
- **Security**: CodeQL analysis for security vulnerabilities

## Environments

- **Local Development**: Uses mock Vista API server with test data
- **Production**: Connects to actual Vista API X endpoints
- **Configuration**: Via environment variables (see `.env.example`)

## Support

For detailed information on any topic, refer to the specific documentation file listed above.