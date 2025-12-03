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

4. Start chatting!
   - Type your message in the input box at the bottom
   - Press Enter or click "Send" to submit
   - Select different models from the dropdown
   - Press Ctrl+N to start a new chat
   - Press Ctrl+C to quit

## Keyboard Shortcuts

- `Enter` - Send message
- `Ctrl+N` - Start new chat (clears history)
- `Ctrl+C` - Quit application

## Development

```bash
# Install with UV
uv sync

# Run in development mode
uv run python -m open_terminalui.main
```

## Project Structure

```
open-terminalui/
├── open_terminalui/
│   ├── __init__.py
│   └── main.py          # Main application code
├── pyproject.toml       # Project configuration
├── README.md
└── .gitignore
```

## Troubleshooting

### No models found

If you see "No models found", make sure you have pulled at least one model:

```bash
ollama pull llama2
ollama pull mistral
ollama pull codellama
```

### Connection error

Make sure Ollama is running:

```bash
ollama serve
```

The default Ollama API runs on `http://localhost:11434`.

## License

MIT
