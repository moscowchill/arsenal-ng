#!/usr/bin/env bash
# Arsenal Shell Integration
# Source this file in your .bashrc or .zshrc to enable auto-prefill without TIOCSTI
#
# Installation:
#   For bash: echo 'source /path/to/arsenal_shell_integration.sh' >> ~/.bashrc
#   For zsh:  echo 'source /path/to/arsenal_shell_integration.sh' >> ~/.zshrc
#   Then restart your shell or run: source ~/.bashrc  (or ~/.zshrc)

# Set environment variable to enable shell integration
export ARSENAL_SHELL_INTEGRATION=1

# Find the arsenal executable
_ARSENAL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-${(%):-%x}}")" && pwd)"
if [ -x "$_ARSENAL_DIR/run" ]; then
    _ARSENAL_CMD="$_ARSENAL_DIR/run"
elif command -v arsenal &>/dev/null; then
    _ARSENAL_CMD="arsenal"
else
    echo "Warning: Cannot find arsenal executable"
    _ARSENAL_CMD="arsenal"
fi

# Wrapper function for arsenal
if [ -n "$BASH_VERSION" ]; then
    # Bash-specific wrapper
    arsenal() {
        local arsenal_cmd_file="$HOME/.arsenal_cmd"
        rm -f "$arsenal_cmd_file"

        # Call the real arsenal command
        "$_ARSENAL_CMD" "$@"
        local exit_code=$?

        # Check if a command was written
        if [ -f "$arsenal_cmd_file" ]; then
            local cmd=$(cat "$arsenal_cmd_file")
            rm -f "$arsenal_cmd_file"

            # For bash 4.0+: Use read -e -i to prefill and let user edit
            if [[ ${BASH_VERSINFO[0]} -ge 4 ]]; then
                echo "[Arsenal] Command ready - press Enter to execute or edit as needed:"
                read -e -i "$cmd" -p "$ " executed_cmd
                if [ -n "$executed_cmd" ]; then
                    # Add to history
                    history -s "$executed_cmd"
                    # Execute the command
                    eval "$executed_cmd"
                fi
            else
                # Fallback for older bash versions
                echo "[Arsenal] Command: $cmd"
                echo "[Arsenal] Bash 4.0+ required for auto-prefill. Copy the command above."
            fi
        fi

        return $exit_code
    }

elif [ -n "$ZSH_VERSION" ]; then
    # Zsh-specific wrapper
    arsenal() {
        local arsenal_cmd_file="$HOME/.arsenal_cmd"
        rm -f "$arsenal_cmd_file"

        # Call the real arsenal command
        "$_ARSENAL_CMD" "$@"
        local exit_code=$?

        # Check if a command was written
        if [ -f "$arsenal_cmd_file" ]; then
            local cmd=$(cat "$arsenal_cmd_file")
            rm -f "$arsenal_cmd_file"

            # Use print -z to push command to the buffer stack
            # This prefills the next command line with the command
            print -z "$cmd"
            echo "[Arsenal] Command prefilled in your prompt - press Enter or edit as needed"
        fi

        return $exit_code
    }

else
    # Generic wrapper for other shells
    arsenal() {
        local arsenal_cmd_file="$HOME/.arsenal_cmd"
        rm -f "$arsenal_cmd_file"

        # Call the real arsenal command
        "$_ARSENAL_CMD" "$@"
        local exit_code=$?

        # Check if a command was written
        if [ -f "$arsenal_cmd_file" ]; then
            local cmd=$(cat "$arsenal_cmd_file")
            rm -f "$arsenal_cmd_file"
            echo "[Arsenal] Command: $cmd"
            echo "[Arsenal] Your shell doesn't support auto-prefill. Please copy the command above."
        fi

        return $exit_code
    }
fi

# Alias 'a' for convenience
alias a='arsenal'
