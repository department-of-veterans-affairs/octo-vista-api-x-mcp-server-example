# Development Container Setup

Simple devcontainer for Windows users to access mise, uv, and other development tools.

## Prerequisites

1. **Podman Desktop** installed on Windows
2. **VS Code** with Dev Containers extension
3. Podman machine running:

   ```powershell
   podman machine init
   podman machine start
   ```

## Quick Start

> **Note**: After pulling updates, rebuild the container to apply changes:
> F1 → "Dev Containers: Rebuild Container"

### 1. Configure VS Code

Add to VS Code settings.json:

```json
{
  "dev.containers.dockerPath": "podman"
}
```

### 2. Start Mock Server and Podman API (Windows Host)

```powershell
cd scripts
.\mock-server.ps1 start
# This starts both the mock server AND exposes Podman API for devcontainer
```

### 3. Open in Dev Container

1. Open project in VS Code
2. Press F1 → "Dev Containers: Reopen in Container"
3. Wait for container to build (first time: ~3-5 minutes)

### 4. Verify Setup (Inside Container)

```bash
# Check Docker connectivity to Podman
docker version
```

### 5. Run the Project (Inside Container)

```bash
# Development with mock server
mise run dev-with-mock

# Run tests
mise run test

# Run linting
mise run lint
```

## Container Features

- Python 3.12 with uv package manager
- Node.js 20 (for MCP dev server)
- mise for tool version management
- Docker client (connects to Podman)
- Access to mock server running on host
- Persistent cache for dependencies

## Troubleshooting

### Permission Errors (mise cache)

If you see `Permission denied` errors:

1. Rebuild the container: F1 → "Dev Containers: Rebuild Container"
2. Or manually fix permissions inside container:

   ```bash
   mkdir -p ~/.cache/mise ~/.cache/uv ~/.mise
   chmod -R 755 ~/.cache ~/.mise
   ```

### Mock server not accessible

- Ensure it's running: `.\scripts\mock-server.ps1 status`
- Check logs: `podman logs vista-api-x-mock`
- Try using `127.0.0.1:8888` instead of `localhost:8888`

### Docker command not working

If `docker version` fails inside the devcontainer:

1. Ensure mock server script is running: `.\scripts\mock-server.ps1 status`
2. If API not responding, restart: `.\scripts\mock-server.ps1 stop` then `start`
3. Rebuild the container: F1 → "Dev Containers: Rebuild Container"
4. The Docker client in the container connects to Podman via TCP port 2375

### Git shows modified files (SOLVED)

The devcontainer automatically configures Git to handle Windows CRLF line endings.
After container starts, Git will show clean status.
If needed, run: `git config --global core.autocrlf input`

### Container build fails

- Clear Podman volumes: `podman volume prune`
- Clear Podman cache: `podman system prune -a`
- Rebuild: F1 → "Dev Containers: Rebuild Container"

## Architecture

```text
Windows Host
├── Podman Desktop (WSL2)
│   ├── Mock Server (localhost:8888)
│   └── Podman API (port 2375)
└── VS Code Dev Container
    ├── Python 3.12 + uv
    ├── Node.js 20 + npm
    ├── Docker client → Podman API
    ├── mise (tool management)
    └── MCP Server Code
```

## Ports

- **2375**: Podman API (Docker compatibility)
- **8000**: MCP Server
- **8888**: Mock Vista API
- **4566**: LocalStack (DynamoDB)
- **8001**: DynamoDB Admin UI
