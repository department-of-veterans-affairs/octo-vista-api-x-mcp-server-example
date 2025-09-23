# Logging Configuration

## Overview

This project implements a comprehensive logging system that is **MCP-compliant** and follows the [Model Context Protocol debugging guidelines](https://modelcontextprotocol.io/legacy/tools/debugging).

## Key Features

- **MCP-Native Logging**: Uses MCP's built-in logging mechanism when available
- **File-Based Logging**: Structured JSON logs with rotation
- **HIPAA Compliance**: Automatic masking of sensitive patient data
- **Performance Tracking**: RPC call timing and audit trails
- **Protocol Safety**: Console logging disabled by default to avoid MCP protocol interference

## Implementation Status

✅ **COMPLETED** - All logging improvements have been implemented:

- ✅ Console logging disabled by default to prevent MCP protocol interference (automatically enabled for local `mise dev*` tasks via Rich console output)
- ✅ MCP-native logging implemented with fallback to file logging
- ✅ Structured JSON logging with HIPAA compliance (file handler optional via `DISABLE_FILE_LOGGING`)
- ✅ Server updated to use MCP-native logging for initialization
- ✅ All existing logging calls updated to use new configuration
- ✅ Debug mode implemented (disables data redaction for development)

## MCP Compliance

### Console Logging

- **Disabled by default** to prevent interference with MCP protocol communication
- Only enabled when `ENABLE_CONSOLE_LOGGING=true` is set
- All logs go to stderr (not stdout) when console logging is enabled

### MCP-Native Logging

The server uses MCP's built-in logging mechanism:

```python
from src.logging_config import log_mcp_message

log_mcp_message(server_instance, "info", "Server started successfully")
```

This ensures logs are properly captured by MCP clients like Claude Desktop.

### Implementation Details

The logging system is implemented in `src/logging_config.py` with the following key components:

- **HIPAAFormatter**: JSON formatter with automatic data masking
- **get_logger()**: MCP-compliant logger factory
- **log_mcp_message()**: MCP-native logging with fallback
- **log_rpc_call()**: Structured RPC call logging
- **log_patient_access()**: HIPAA-compliant patient access logging

The system automatically masks sensitive data patterns:

- SSNs: `123-45-6789` → `[REDACTED-SSN]`
- DFNs: `AB123456` → `[REDACTED-DFN]`
- IP addresses: `192.168.1.1` → `[REDACTED-IP]`
- 9-digit numbers: `123456789` → `[REDACTED-9DIGIT]`

### Debug Mode

When `VISTA_MCP_DEBUG=true` is set, data redaction is disabled for development and troubleshooting:

```bash
# Enable debug mode (disables data redaction)
export VISTA_MCP_DEBUG=true

# Disable debug mode (enables data redaction - default)
export VISTA_MCP_DEBUG=false
```

**Warning**: Debug mode should only be used in development environments. Never enable debug mode in production as it will log sensitive patient data.

### Security Considerations

- **Production**: Always keep `VISTA_MCP_DEBUG=false` in production environments
- **Development**: Use `VISTA_MCP_DEBUG=true` only for troubleshooting and development
- **Log Files**: Ensure log files are properly secured and rotated in all environments
- **Access Control**: Limit access to log files containing sensitive data

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `LOG_FORMAT` | `json` | Log format (`json` or `text`) |
| `LOG_FILE` | `logs/octo-vista.log` | Path to log file |
| `DISABLE_FILE_LOGGING` | `false` | Set to `true` to skip the rotating file handler (useful for sandboxed environments) |
| `ENABLE_CONSOLE_LOGGING` | `false` | Enable console logging (stderr). Automatically enabled for local mise `dev*` tasks. |
| `VISTA_MCP_DEBUG` | `false` | Enable debug mode (disables data redaction for development) |

### MCP-Specific Settings

For MCP servers, the following settings are recommended:

```bash
# Disable console logging (default)
ENABLE_CONSOLE_LOGGING=false

# Enable file logging
LOG_FILE=logs/octo-vista.log

# Use JSON format for structured logging
LOG_FORMAT=json
```

## Usage

### Basic Logging

```python
from src.logging_config import get_logger

logger = get_logger("my-module")
logger.info("This is an info message")
logger.error("This is an error message")
```

### MCP-Native Logging

```python
from src.logging_config import log_mcp_message

# Log to MCP client
log_mcp_message(server_instance, "info", "Operation completed", 
                operation="patient_search", duration_ms=150)
```

### Structured Logging

```python
from src.logging_config import log_with_context

log_with_context(logger, "info", "User action", 
                user_id="12345", action="login", station="500")
```

### RPC Call Logging

```python
from src.logging_config import log_rpc_call

log_rpc_call(
    logger=logger,
    rpc_name="ORWU GETPATIENT",
    station="500",
    duz="10000000219",
    duration_ms=150,
    success=True
)
```

### Patient Access Logging (HIPAA Compliant)

```python
from src.logging_config import log_patient_access

log_patient_access(
    logger=logger,
    patient_dfn="123456789",  # Will be masked in logs
    action="view_medications",
    user_duz="10000000219",
    station="500",
    success=True
)
```

## Log Output Examples

### JSON Format (Default)

```json
{
  "timestamp": "2025-08-07T14:01:44.094714",
  "level": "INFO",
  "logger": "mcp-server",
  "message": "RPC call: ORWU GETPATIENT",
  "module": "logging_config",
  "function": "log_with_context",
  "line": 184,
  "rpc_name": "ORWU GETPATIENT",
  "station": "500",
  "duz": "10000000219",
  "success": true,
  "duration_ms": 150
}
```

### Text Format

```
2025-08-07 14:01:44,094 - mcp-server - INFO - RPC call: ORWU GETPATIENT
```

## HIPAA Compliance

### Automatic Data Masking

The logging system automatically masks sensitive data:

- **SSNs**: `123-45-6789` → `[REDACTED]`
- **DFNs**: `AB123456` → `[REDACTED-3456]`
- **IP Addresses**: `192.168.1.1` → `[REDACTED]`
- **9-digit numbers**: Potential SSNs are masked

### Patient Access Audit Trail

All patient data access is logged with:

- Masked patient identifiers
- User authentication details
- Action performed
- Success/failure status
- Timestamp and context

## Log Rotation

- **File Size**: 10MB maximum per log file
- **Backup Count**: 5 backup files kept
- **Location**: `logs/octo-vista.log` and rotated files
- **Encoding**: UTF-8

## Testing

### Test Logging Configuration

```bash
python test_logging.py
```

### Test MCP Compliance

```bash
python test_mcp_logging.py
```

### Test Debug Mode

```bash
# Test with debug mode disabled (default)
export VISTA_MCP_DEBUG=false
python -c "from src.logging_config import get_logger; logger = get_logger('test'); logger.info('Patient SSN: 123-45-6789')"

# Test with debug mode enabled
export VISTA_MCP_DEBUG=true
python -c "from src.logging_config import get_logger; logger = get_logger('test'); logger.info('Patient SSN: 123-45-6789')"
```

### Verify No Console Interference

```bash
# Should not output JSON to stdout
python test_mcp_logging.py | grep -v "timestamp"
```

## Integration with Monitoring

### Log Aggregation

- JSON format enables easy parsing by log aggregation tools
- Structured fields allow for advanced filtering and alerting
- HIPAA-compliant masking ensures compliance in centralized logging

### Performance Monitoring

- RPC call timing is automatically logged
- Error rates and patterns can be tracked
- Resource usage can be monitored through structured logs

## Troubleshooting

### Common Issues

1. **Missing Console Output**
   - Set `ENABLE_CONSOLE_LOGGING=true` (and optionally `DISABLE_FILE_LOGGING=true` in read-only containers)
   - Logs are emitted on stderr; confirm your runtime captures stderr in CloudWatch/Datadog

2. **Missing Log Files**
   - Verify `logs/` directory exists
   - Check file permissions
   - Ensure `LOG_FILE` path is correct

3. **Performance Issues**
   - Reduce log level to `WARNING` in production
   - Monitor log file sizes
   - Consider log rotation settings

### Debug Mode

Enable debug logging for troubleshooting:

```bash
export LOG_LEVEL=DEBUG
export VISTA_MCP_DEBUG=true
```

## Best Practices

1. **Use MCP-Native Logging**: Prefer `log_mcp_message()` for server events
2. **Structured Logging**: Use JSON format for better parsing
3. **HIPAA Compliance**: Always use patient access logging for sensitive data
4. **Performance**: Log at appropriate levels (INFO for normal operations, DEBUG for troubleshooting)
5. **Security**: Never log credentials or sensitive configuration
6. **Monitoring**: Use structured fields for alerting and metrics

## References

- [MCP Debugging Documentation](https://modelcontextprotocol.io/legacy/tools/debugging)
- [Python Logging Documentation](https://docs.python.org/3/library/logging.html)
- [HIPAA Logging Guidelines](https://www.hhs.gov/hipaa/for-professionals/privacy/guidance/index.html)
