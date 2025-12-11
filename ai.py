#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import requests
import subprocess
import sys
import json
import shlex
import os
from dotenv import load_dotenv

# --- Default Configuration (used if .env not found or var missing) ---
DEFAULT_OLLAMA_API_URL = "http://localhost:11434/api/generate"
DEFAULT_OLLAMA_MODEL = "gemma3:1b"

# --- Configuration Loading ---
def load_configuration():
    """
    Loads configuration from .env file located in the script's directory,
    environment variables, and script defaults.
    Precedence: CLI args > Environment Vars > .env file > Script Defaults
    """
    # Find the directory where the script is located
    script_dir = os.path.dirname(os.path.realpath(__file__))
    dotenv_path = os.path.join(script_dir, '.env')

    # Load the .env file if it exists. Environment variables can still override.
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path=dotenv_path)
    # else:
        # Optionally, print a warning if .env is not found on first load attempt
        # print("Warning: '.env' file not found in script directory. Using defaults or environment variables.", file=sys.stderr)
        # pass # Continue with defaults or environment variables

    # Get settings: environment variable > .env file (loaded above) > script default
    api_url = os.getenv('OLLAMA_API_URL', DEFAULT_OLLAMA_API_URL)
    default_model = os.getenv('OLLAMA_DEFAULT_MODEL', DEFAULT_OLLAMA_MODEL)

    # Check if we are using the hardcoded defaults (meaning nothing was found in env or .env)
    using_defaults = api_url == DEFAULT_OLLAMA_API_URL and default_model == DEFAULT_OLLAMA_MODEL
    if not os.path.exists(dotenv_path) and using_defaults:
         print("Info: No '.env' file found and no environment variables set. Using default settings.", file=sys.stderr)
         print(f"Info: Consider copying '.env.example' to '.env' in {script_dir} and customizing it.", file=sys.stderr)


    return api_url, default_model

# Load configuration early
OLLAMA_API_URL, OLLAMA_DEFAULT_MODEL = load_configuration()

# This global will be updated if --model is passed via CLI
CURRENT_OLLAMA_MODEL = OLLAMA_DEFAULT_MODEL


# Commands considered dangerous that will require user confirmation
DESTRUCTIVE_COMMANDS = [
    "rm", "mv", "kill", "pkill", "killall", "shutdown", "reboot", "halt",
    "shred", "dd", "mkfs", "fdisk", "userdel", "groupdel", "chmod", "chown",
    "sudo", "su", "docker rm", "docker rmi", "kubectl delete",
]

# --- Functions (query_ollama, is_destructive, execute_command remain the same as the previous version) ---

def query_ollama(prompt_text):
    """Sends the prompt to Ollama and returns the model's response."""
    # Prompt designed to ask ONLY for the Linux command
    system_prompt = """
    You are an expert Linux assistant. Your sole task is to translate the user's request
    into a SINGLE executable Linux terminal command.
    DO NOT add explanations, ANY introductory or concluding text, ANY notes.
    DO NOT use markdown formatting (like ```bash ... ```).
    ONLY return the pure, executable Linux command.
    If the request cannot be reasonably translated into a Linux command or is ambiguous,
    return the string 'ERROR: Could not generate command.'.

    Examples:
    User: I want to know the size of the current folder
    Assistant: du -sh .
    User: list the files in long format
    Assistant: ls -l
    User: delete the temporary file
    Assistant: rm temporary.log
    User: What's the weather like?
    Assistant: ERROR: Could not generate command.
    """

    full_prompt = f"{system_prompt}\nUser: {prompt_text}\nAssistant:"

    payload = {
        "model": CURRENT_OLLAMA_MODEL, # Use the current model (potentially overridden by CLI)
        "prompt": full_prompt,
        "stream": False,
        "keep_alive": 0,
        "options": {
            "temperature": 0.1,
            "stop": ["\nUser:", "\nAssistant:"]
        }
    }
    headers = {'Content-Type': 'application/json'}

    print(f" Sending prompt to Ollama (model: {CURRENT_OLLAMA_MODEL}, API: {OLLAMA_API_URL})...")

    try:
        response = requests.post(OLLAMA_API_URL, json=payload, headers=headers, timeout=60)
        response.raise_for_status()

        data = response.json()
        command = data.get("response", "").strip()

        # (Cleanup logic remains the same)
        lines = command.split('\n')
        potential_command = ""
        for line in lines:
            clean_line = line.strip()
            if clean_line and not clean_line.lower().startswith(("here is", "the command is", "`", "#")):
                if clean_line.startswith("```") and clean_line.endswith("```"):
                    clean_line = clean_line[3:-3].strip()
                    if clean_line.lower().startswith("bash"):
                         clean_line = clean_line[4:].strip()
                elif clean_line.startswith("`") and clean_line.endswith("`"):
                     clean_line = clean_line[1:-1].strip()
                potential_command = clean_line
                break

        if not potential_command or "ERROR:" in potential_command:
             print(f"Error: The model failed to generate a valid command.", file=sys.stderr)
             print(f"Raw model response: {command}", file=sys.stderr)
             return None

        return potential_command

    except requests.exceptions.ConnectionError:
        print(f"Error: Could not connect to Ollama at {OLLAMA_API_URL}", file=sys.stderr)
        print("Make sure Ollama is running and the API URL in your config/environment is correct.", file=sys.stderr)
        return None
    except requests.exceptions.Timeout:
        print(f"Error: Timeout waiting for Ollama response.", file=sys.stderr)
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error in Ollama request: {e}", file=sys.stderr)
        try:
            error_details = response.json()
            print(f"Ollama error details: {error_details}", file=sys.stderr)
        except:
             pass
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON response from Ollama.", file=sys.stderr)
        print(f"Received response: {response.text}", file=sys.stderr)
        return None

def is_destructive(command):
    """Checks if the command seems destructive."""
    if not command:
        return False
    try:
        command_parts = shlex.split(command)
        if not command_parts:
            return False
        first_command = command_parts[0]
        if first_command == 'sudo' and len(command_parts) > 1:
             actual_command = command_parts[1]
             print(f"Warning: Command uses 'sudo'.")
             return True
        else:
             actual_command = first_command
        for destructive in DESTRUCTIVE_COMMANDS:
             if actual_command == destructive or command.strip().startswith(destructive + " "):
                return True
    except ValueError:
         print(f"Warning: Could not properly parse command '{command}' for safety check.", file=sys.stderr)
         return True
    return False

def execute_command(command):
    """Executes the command in the shell and displays the output."""
    print(f"\n Executing: {command}")
    print("-" * 20)
    try:
        result = subprocess.run(command, shell=True, check=False, capture_output=True, text=True, encoding='utf-8', errors='replace')
        if result.stdout:
            print("Output (stdout):")
            print(result.stdout)
        if result.stderr:
            print("Errors (stderr):", file=sys.stderr)
            print(result.stderr, file=sys.stderr)
        if result.returncode != 0:
            print(f"\nWarning! Command finished with error code: {result.returncode}", file=sys.stderr)
    except Exception as e:
        print(f"\nError trying to execute the command: {e}", file=sys.stderr)

# --- Main Logic ---

def main():
    # Argument parser uses the loaded default model from config/script
    parser = argparse.ArgumentParser(
        description="AI assistant to generate and execute Linux commands via Ollama.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter # Shows default values in help
    )
    parser.add_argument("-p", "--prompt", required=True, help="Natural language description of the desired command.")
    parser.add_argument("-i", "--interactive", action="store_true", help="Ask for confirmation before executing the command.")
    parser.add_argument("-y", "--yes", action="store_true", help="Skip confirmation when used with -i (USE WITH EXTREME CAUTION!).")
    parser.add_argument("--model", default=OLLAMA_DEFAULT_MODEL,
                        help="Ollama model name to use for this execution.")

    args = parser.parse_args()

    # Update the global model variable *if* provided via command line
    global CURRENT_OLLAMA_MODEL
    CURRENT_OLLAMA_MODEL = args.model

    # The rest of the main function remains the same
    command_to_run = query_ollama(args.prompt)

    if not command_to_run:
        sys.exit(1)

    print(f"\n Suggested command: \033[1;34m{command_to_run}\033[0m") # Blue and bold

    # By default, don't execute commands unless -i flag is provided
    execute = False
    
    if args.interactive:
        destructive = is_destructive(command_to_run)
        
        if destructive and not args.yes:
            try:
                confirm = input(f"\n\033[1;31m WARNING!\033[0m This command appears destructive or requires elevated privileges.\n Do you want to execute it anyway? (y/N): ")
                if confirm.lower() == 'y':
                    execute = True
                else:
                    print(" Execution cancelled by user.")
            except (EOFError, KeyboardInterrupt):
                print("\n Execution cancelled.")
                sys.exit(0)
        elif destructive and args.yes:
            print("\n\033[1;31m WARNING!\033[0m Executing destructive command without confirmation due to -y flag.")
            execute = True
        elif not args.yes:
            try:
                confirm = input(f"\n Do you want to execute this command? (y/N): ")
                if confirm.lower() == 'y':
                    execute = True
                else:
                    print(" Execution cancelled by user.")
            except (EOFError, KeyboardInterrupt):
                print("\n Execution cancelled.")
                sys.exit(0)
        else:
            # -i and -y both provided, execute without confirmation
            execute = True
    else:
        print("\n Command not executed. Use -i flag to execute with confirmation.")

    if execute:
        execute_command(command_to_run)

if __name__ == "__main__":
    main()
