# AI Command Helper For Linux

A simple command-line tool that uses a local **Ollama** model to translate natural language prompts into Linux commands and optionally execute them.

## Features

*   **Natural Language to Command:** Describe what you want to do, and the AI suggests the Linux command.
*   **Ollama Integration:** Leverages locally running Ollama models (like `gemma3`, `llama3.2`, etc.).
*   **Safe by Default:** Commands are displayed but **not executed** unless you explicitly use the `-i` flag.
*   **Interactive Execution:** Use `-i` to execute commands with confirmation prompts.
*   **Safety Confirmation:** Prompts for user confirmation before executing potentially destructive commands (e.g., `rm`, `kill`, `sudo`).
*   **Configurable:** Set your default Ollama model and API endpoint via an `.env` file.
*   **Command-line Interface:** Easy to use via `ai -p "your prompt"`.
*   **Fast Environment Management:** Uses [`uv`](https://github.com/astral-sh/uv) for quick virtual environment creation and dependency installation.

## Prerequisites

*   **Python 3:** Version 3.8 or higher recommended (compatible with `uv`).
*   **uv:** The fast Python package installer and resolver. See installation instructions: [https://github.com/astral-sh/uv#installation](https://github.com/astral-sh/uv#installation).
    *   *Example installation (macOS/Linux):* `curl -LsSf https://astral.sh/uv/install.sh | sh`
    *   *Example installation (Windows):* `irm https://astral.sh/uv/install.ps1 | iex`
*   **Ollama:** Must be installed and running. Make sure you have downloaded a model (e.g., `ollama pull gemma3`). See [Ollama GitHub](https://github.com/ollama/ollama).

## Installation & Setup (Using uv)

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd your-project-name
    ```

2.  **Create and activate the virtual environment using `uv`:**
    *   This command creates a virtual environment named `.venv` in the current directory.
    ```bash
    uv venv
    ```
    *   Activate the environment:
        *   **Linux/macOS (bash/zsh):**
            ```bash
            source .venv/bin/activate
            ```
        *   **Windows (Command Prompt):**
            ```cmd
            .venv\Scripts\activate.bat
            ```
        *   **Windows (PowerShell):**
            ```powershell
            .venv\Scripts\Activate.ps1
            ```
        *(Your terminal prompt should now indicate that you are inside the `.venv` environment)*

3.  **Install dependencies using `uv`:**
    *   This reads the `requirements.txt` file and installs the packages into the activated environment.
    ```bash
    uv pip install -r requirements.txt
    ```

4.  **Configure:**
    *   Copy the example environment file:
        ```bash
        cp .env.example .env
        ```
    *   Edit the `.env` file with your preferred text editor and set your `OLLAMA_API_URL` (if different from the default `http://localhost:11434/api/generate`) and your desired `OLLAMA_DEFAULT_MODEL`.
        ```dotenv
        # .env
        OLLAMA_API_URL=http://localhost:11434/api/generate
        OLLAMA_DEFAULT_MODEL=codellama # Or llama3, mistral, etc.
        ```
        **Note:** The `.env` file is ignored by Git (via `.gitignore`) and should not be committed.

5.  **Make the script executable (Linux/macOS):**
    ```bash
    chmod +x ai.py
    ```

6.  **(Optional but Recommended) Add to PATH:**
    To run the tool simply as `ai` from any directory, you can either:
    *   Create a symbolic link in a directory already in your PATH:
        ```bash
        # Example: linking to /usr/local/bin
        sudo ln -s "$(pwd)/ai" /usr/local/bin/ai
        ```
    *   Or, add the project directory itself to your PATH variable (by editing `~/.bashrc`, `~/.zshrc`, etc.).
        ```bash
        export PATH="$PATH:/path/to/your-project-name"
        ```
        Remember to reload your shell configuration (`source ~/.bashrc`) after editing.

## Usage on the CLI

Once the setup is complete, you can run the AI helper directly from any directory in your terminal. You **do not** need to activate the `.venv` environment manually.

```bash
ai -p "YOUR PROMPT IN NATURAL LANGUAGE" [OPTIONS]
```

### Options:

**-p, --prompt (Required):** The description of the command you want (e.g., "list files sorted by size").

**-i, --interactive:** Ask for confirmation before executing the generated command. **Required to execute commands** - by default, commands are only displayed, not executed.

**--model MODEL_NAME:** Specify an Ollama model to use for this specific execution, overriding the default from .env. (e.g., ai --model llama3 -p "show current processes"). The default value is loaded from your .env file.

**-y, --yes:** DANGEROUS! When used with `-i`, skips confirmation prompts and executes commands immediately. Use with extreme caution.

## Usage on the project workspace:

**Important:** Ensure your `uv` virtual environment is activated (`source .venv/bin/activate` or equivalent) before running the script.

```bash
python ai.py -p "YOUR PROMPT IN NATURAL LANGUAGE" [OPTIONS]
```

## Disclaimer

**Security Warning**
🚨 Executing commands generated by an AI, especially on your own system, carries inherent risks. 🚨

The AI might misunderstand your prompt and generate unintended or harmful commands.

**By default, commands are NOT executed** - they are only displayed for your review. You must use the `-i` flag to execute commands.

Always review the suggested command carefully before confirming execution.

The list of **DESTRUCTIVE_COMMANDS** in the script is a safeguard but **may not be exhaustive**. Commands involving sudo are always flagged.

Use the `-y` flag with EXTREME CAUTION. You are solely responsible for the consequences of the commands executed.

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.
