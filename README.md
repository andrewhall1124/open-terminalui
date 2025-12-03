# Open Terminal UI

A terminal-based interface for interacting with Ollama and local LLM models, built with Textual.

## Requirements

- Python 3.13+
- [Ollama](https://ollama.ai/) installed and running
- At least one Ollama model pulled (e.g., `ollama pull llama2`)

## Installation

Using UV (recommended):

```bash
# Install dependencies
uv sync

# Run the application
uv run open-terminalui
```

## Usage

1. Make sure Ollama is running:
   ```bash
   ollama serve
   ```

2. Pull a model if you haven't already:
   ```bash
   ollama pull llama2
   ```

3. Launch Open Terminal UI:
   ```bash
   uv run open-terminalui
   ```
