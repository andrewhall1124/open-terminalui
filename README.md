# open-terminalui

[![PyPI - Version](https://img.shields.io/pypi/v/open-terminalui.svg)](https://pypi.org/project/open-terminalui)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/open-terminalui.svg)](https://pypi.org/project/open-terminalui)

![open-terminalui screenshot](artifacts/open-terminalui.png)

-----

**open-terminalui** is a modern terminal-based user interface for interacting with local LLMs powered by Ollama. It provides an intuitive chat interface with document management, vector search capabilities, and a clean, responsive design built with Textual.

## Table of Contents

- [Installation](#installation)
  - [Prerequisites](#prerequisites)
- [Development](#development)
- [License](#license)

## Installation

### Prerequisites

`open-terminalui` requires Ollama to run local LLMs. Follow these steps to set up your environment:

#### 1. Install Ollama

Visit [https://ollama.ai](https://ollama.ai) and download Ollama for your operating system, or use the following commands:

**macOS:**
```bash
brew install ollama
```

**Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**Windows:**
Download the installer from [https://ollama.ai/download](https://ollama.ai/download)

#### 2. Pull the Llama 3.2 Model

After installing Ollama, pull the llama3.2 model:

```bash
ollama pull llama3.2
```

#### 3. Start Ollama

Start the Ollama service:

```bash
ollama serve
```

Note: On macOS and Windows, Ollama typically starts automatically. On Linux, you may need to run this command or set it up as a service.

#### 4. Install open-terminalui

Install `open-terminalui` using pipx:

```bash
pipx install open-terminalui
```

If you don't have pipx installed, you can install it with:

```bash
# macOS
brew install pipx
pipx ensurepath

# Linux
python3 -m pip install --user pipx
python3 -m pipx ensurepath

# Windows
python -m pip install --user pipx
python -m pipx ensurepath
```

#### 5. Run open-terminalui

Launch the application:

```bash
open-terminalui
```

The terminal UI will start and connect to your local Ollama instance running llama3.2.

## Development

### Installation

```bash
uv sync
```

### Testing

```bash
textual run --dev open_terminalui.entry_points:app
```

In a seperate console
```bash
textual console  # All logs
textual console -x SYSTEM -x EVENT -x DEBUG -x INFO # Minimal logs
```

## License

`open-terminalui` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
