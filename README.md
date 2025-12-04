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
```

## Development

Run textual app in development mode

```bash
textual run --dev open_terminalui:main
```
