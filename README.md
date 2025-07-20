# terminal-sherpa

A lightweight AI chat interface for fellow terminal dwellers.

Turn natural language into bash commands instantly.
Stop googling syntax and start asking.

[![PyPI - Version](https://img.shields.io/pypi/v/terminal-sherpa)](https://pypi.python.org/pypi/terminal-sherpa)
[![GitHub License](https://img.shields.io/github/license/lcford2/terminal-sherpa)](https://github.com/lcford2/terminal-sherpa/blob/main/LICENSE)
[![Python Versions](https://img.shields.io/pypi/pyversions/terminal-sherpa)](https://pypi.python.org/pypi/terminal-sherpa)
[![Actions status](https://github.com/lcford2/terminal-sherpa/actions/workflows/main.yml/badge.svg)](https://github.com/lcford2/terminal-sherpa/actions)
[![codecov](https://codecov.io/github/lcford2/terminal-sherpa/graph/badge.svg?token=2MXHNL3RHE)](https://codecov.io/github/lcford2/terminal-sherpa)

## 🚀 Getting Started

Get up and running:

```bash
# Install terminal-sherpa
pip install terminal-sherpa # installs the `ask` CLI tool

# Set your API key
export ANTHROPIC_API_KEY="your-key-here"

# Try it out
ask "find all .py files modified in the last week"
```

**Example output:**

```bash
find . -name "*.py" -mtime -7
```

## ✨ Features

- **Natural language to bash conversion** - Describe what you want, get the command
- **Multiple AI provider support** - Choose between Anthropic (Claude), OpenAI (GPT), Google (Gemini), xAI (Grok) models, and local models via Ollama
- **Flexible configuration system** - Set defaults, customize models, and manage API keys
- **XDG-compliant config files** - Follows standard configuration file locations
- **Verbose logging support** - Debug and understand what's happening under the hood

## 📦 Installation

### Requirements

- Python 3.9+
- API key for Anthropic, OpenAI, Google, or xAI (or local Ollama installation)

### Install Methods

**Using pip:**

```bash
pip install terminal-sherpa
```

**From source:**

```bash
git clone https://github.com/lcford2/terminal-sherpa.git
cd terminal-sherpa
uv sync
uv run ask "your prompt here"
```

**Verify installation:**

```bash
ask --help
```

## 💡 Usage

### Basic Syntax

```bash
ask "your natural language prompt"
```

### Command Options

| Option                   | Description                | Example                                     |
| ------------------------ | -------------------------- | ------------------------------------------- |
| `--model provider:model` | Specify provider and model | `ask --model anthropic "list files"`        |
|                          |                            | `ask --model anthropic:sonnet "list files"` |
|                          |                            | `ask --model openai "list files"`           |
|                          |                            | `ask --model gemini "list files"`           |
|                          |                            | `ask --model gemini:pro "list files"`       |
|                          |                            | `ask --model grok "list files"`             |
|                          |                            | `ask --model ollama "list files"`           |
|                          |                            | `ask --model ollama:codellama "list files"` |
| `--verbose`              | Enable verbose logging     | `ask --verbose "compress this folder"`      |

### Practical Examples

**File Operations:**

```bash
ask "find all files larger than 100MB"
# Example output: find . -size +100M

ask "create a backup of config.txt with timestamp"
# Example output: cp config.txt config.txt.$(date +%Y%m%d_%H%M%S)
```

**Git Commands:**

```bash
ask "show git log for last 5 commits with one line each"
# Example output: git log --oneline -5

ask "delete all local branches that have been merged"
# Example output: git branch --merged | grep -v "\*\|main\|master" | xargs -n 1 git branch -d
```

**System Administration:**

```bash
ask "check disk usage of current directory sorted by size"
# Example output: du -sh * | sort -hr

ask "find processes using port 8080"
# Example output: lsof -i :8080
```

**Text Processing:**

```bash
ask "count lines in all Python files"
# Example output: find . -name "*.py" -exec wc -l {} + | tail -1

ask "replace all tabs with spaces in file.txt"
# Example output: sed -i 's/\t/    /g' file.txt
```

**Network Operations:**

```bash
ask "download file from URL and save to downloads folder"
# Example output: curl -o ~/Downloads/filename "https://example.com/file"

ask "check if port 443 is open on example.com"
# Example output: nc -zv example.com 443
```

## ⚙️ Configuration

### Configuration File Locations

Ask follows XDG Base Directory Specification:

1. `$XDG_CONFIG_HOME/ask/config.toml`
1. `~/.config/ask/config.toml` (if XDG_CONFIG_HOME not set)
1. `~/.ask/config.toml` (fallback)

### Environment Variables

```bash
export ANTHROPIC_API_KEY="your-anthropic-key"
export OPENAI_API_KEY="your-openai-key"
export GEMINI_API_KEY="your-gemini-key"
export XAI_API_KEY="your-xai-key"
```

### Example Configuration File

Create `~/.config/ask/config.toml`:

```toml
[ask]
default_model = "anthropic"

[anthropic]
model = "claude-3-haiku-20240307"
max_tokens = 512

[anthropic.sonnet]
model = "claude-sonnet-4-20250514"
max_tokens = 1024

[openai]
model = "gpt-4o"
max_tokens = 1024

[gemini]
model = "gemini-2.5-flash-lite-preview-06-17"
max_tokens = 150

[gemini.pro]
model = "gemini-2.5-pro"
max_tokens = 1024

[grok]
model = "grok-3-fast"
max_tokens = 150
temperature = 0.5

[ollama]
model = "llama3.2"
host = "localhost"
port = 11434

[ollama.codellama]
model = "codellama"
```

## 🤖 Supported Providers

- Anthropic (Claude)
- OpenAI (GPT)
- Google (Gemini)
- xAI (Grok)
- Ollama (Local Models)

> **Note:** Get API keys from [Anthropic Console](https://console.anthropic.com/), [OpenAI Platform](https://platform.openai.com/), [Google AI Studio](https://aistudio.google.com/), or [xAI Console](https://x.ai/console)

### Local Models with Ollama

For local inference without API costs:

1. **Install Ollama:** Visit [ollama.ai](https://ollama.ai) for installation instructions
2. **Pull a model:** `ollama pull llama3.2`
3. **Start Ollama:** `ollama serve` (if not auto-started)
4. **Use with ask:** `ask --model ollama "your prompt"`

**Example:**
```bash
ollama pull codellama
ask --model ollama:codellama "optimize this bash script"
```

## 🛣️ Roadmap

- [ ] Shell integration and auto-completion
- [ ] Additional providers (Cohere, Mistral)
- [ ] Additional local model support (llama.cpp)

## 🔧 Development

### Setup

```bash
git clone https://github.com/lcford2/terminal-sherpa.git
cd ask
uv sync --all-groups
uv run pre-commit install
```

### Testing

```bash
uv run python -m pytest
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run pre-commit checks: `uv run pre-commit run --all-files`
5. Run tests: `uv run task test`
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Issues

Found a bug or have a feature request? Please open an issue on [GitHub Issues](https://github.com/lcford2/ask/issues).
