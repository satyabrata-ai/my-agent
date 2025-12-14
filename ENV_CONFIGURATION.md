# Environment Configuration Guide

## Model Configuration Update

The agent model is now configurable via the `.env` file!

## Required Configuration

Add this line to your `.env` file:

```bash
# Model Configuration
AGENT_MODEL=gemini-2.0-flash-exp
```

## To Use Gemini 3 Pro Preview

Update your `.env` file:

```bash
AGENT_MODEL=gemini-3-pro-preview
```

## Complete .env Template

Here's a complete `.env` file template:

```bash
# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=ccibt-hack25ww7-706
GOOGLE_CLOUD_LOCATION=global
GOOGLE_GENAI_USE_VERTEXAI=True
LOGS_BUCKET_NAME=gs://ccibt-agent-logs

# GCS Data Bucket Settings
GCS_DATA_BUCKET=your-bucket-name
GCS_DATASET_PREFIX=datasets/uc4-market-activity-prediction-agent

# Agent Memory Settings
GCS_MEMORY_PATH=agent_memory

# Model Configuration
# Available models:
#   - gemini-2.0-flash-exp (default, fast)
#   - gemini-3-pro-preview (latest, most capable)
#   - gemini-1.5-pro (stable, production)
#   - gemini-1.5-flash (fast, lightweight)
AGENT_MODEL=gemini-2.0-flash-exp

# Environment
ENVIRONMENT=development
```

## How to Change the Model

### Option 1: Edit .env file (Recommended)

1. Open your `.env` file in the project root
2. Find or add the line: `AGENT_MODEL=gemini-2.0-flash-exp`
3. Change it to: `AGENT_MODEL=gemini-3-pro-preview`
4. Save the file
5. Restart the agent

### Option 2: Set Environment Variable

**Windows (PowerShell):**
```powershell
$env:AGENT_MODEL="gemini-3-pro-preview"
```

**Windows (CMD):**
```cmd
set AGENT_MODEL=gemini-3-pro-preview
```

**Linux/Mac:**
```bash
export AGENT_MODEL=gemini-3-pro-preview
```

## Verification

After starting the agent, check the console output:

```
✓ Loaded configuration from /path/to/.env
✓ Configuration validated successfully
```

The agent will now use the model specified in `AGENT_MODEL`.

## Available Models

| Model | Best For | Speed | Cost |
|-------|----------|-------|------|
| `gemini-2.0-flash-exp` | Development, fast iterations | Fastest | Lowest |
| `gemini-3-pro-preview` | Production, best quality | Medium | Higher |
| `gemini-1.5-pro` | Stable production use | Medium | Medium |
| `gemini-1.5-flash` | High volume, simple tasks | Very Fast | Low |

## Files Modified

The following files were updated to support model configuration:

1. **`app/config.py`** - Added `AGENT_MODEL` configuration parameter
2. **`app/agent.py`** - Updated root agent to use `config.AGENT_MODEL`
3. **`app/sub_agents/news_sentiment_agent/agent.py`** - Updated sentiment agent to use `config.AGENT_MODEL`

## Default Value

If `AGENT_MODEL` is not set in `.env`, the agent will default to:
```
AGENT_MODEL=gemini-2.0-flash-exp
```

## Troubleshooting

### Model not found error
If you get a "model not found" error:
- Verify the model name is spelled correctly
- Check that the model is available in your Google Cloud project
- Ensure you have access to preview models if using `gemini-3-pro-preview`

### Configuration not updating
If changes don't take effect:
1. Verify your `.env` file is in the project root
2. Restart the agent completely
3. Check for typos in the variable name (must be exactly `AGENT_MODEL`)

## Testing

After configuring the model, test with:

```bash
# Start the agent
make playground

# In the playground, ask:
"What model are you using?"
```

The agent should respond with the configured model information.
