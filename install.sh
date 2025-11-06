#!/usr/bin/env bash
# Arsenal Shell Integration Installer
# This script installs the shell integration for arsenal auto-prefill

set -e

INTEGRATION_FILE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/arsenal_shell_integration.sh"

echo "=========================================="
echo "Arsenal Shell Integration Installer"
echo "=========================================="
echo

if [ ! -f "$INTEGRATION_FILE" ]; then
    echo "Error: Cannot find arsenal_shell_integration.sh"
    echo "Make sure you're running this script from the arsenal directory"
    exit 1
fi

# Smart shell detection
detect_user_shell() {
    # Check parent process (most reliable for interactive shells)
    local parent_pid=$(ps -o ppid= -p $$ 2>/dev/null | tr -d ' ')
    if [ -n "$parent_pid" ]; then
        local parent_cmd=$(ps -o comm= -p $parent_pid 2>/dev/null | tr -d ' ')
        case "$parent_cmd" in
            *zsh*) echo "zsh"; return ;;
            *bash*) echo "bash"; return ;;
        esac
    fi

    # Check $SHELL environment variable
    case "$(basename "$SHELL" 2>/dev/null)" in
        zsh) echo "zsh"; return ;;
        bash) echo "bash"; return ;;
    esac

    # Check which config file was modified more recently
    if [ -f "$HOME/.zshrc" ] && [ -f "$HOME/.bashrc" ]; then
        if [ "$HOME/.zshrc" -nt "$HOME/.bashrc" ]; then
            echo "zsh"; return
        fi
    elif [ -f "$HOME/.zshrc" ]; then
        echo "zsh"; return
    elif [ -f "$HOME/.bashrc" ]; then
        echo "bash"; return
    fi

    echo ""
}

DETECTED_SHELL=$(detect_user_shell)

if [ -z "$DETECTED_SHELL" ]; then
    echo "Could not auto-detect your shell."
    echo ""
    echo "Which shell do you use?"
    echo "  1) bash"
    echo "  2) zsh"
    echo ""
    read -p "Enter choice (1 or 2): " choice
    case $choice in
        1) SHELL_NAME="bash" ;;
        2) SHELL_NAME="zsh" ;;
        *) echo "Invalid choice"; exit 1 ;;
    esac
else
    SHELL_NAME="$DETECTED_SHELL"
fi

# Set config file
case "$SHELL_NAME" in
    bash) RC_FILE="$HOME/.bashrc" ;;
    zsh) RC_FILE="$HOME/.zshrc" ;;
    *) echo "Error: Unsupported shell: $SHELL_NAME"; exit 1 ;;
esac

echo "Detected shell: $SHELL_NAME"
echo "Config file: $RC_FILE"
echo

# Check if already installed
if grep -q "arsenal_shell_integration.sh" "$RC_FILE" 2>/dev/null; then
    echo "⚠️  Shell integration already installed in $RC_FILE"
    echo
    read -p "Do you want to reinstall? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Installation cancelled."
        exit 0
    fi
    # Remove old integration
    sed -i '/arsenal_shell_integration.sh/d' "$RC_FILE"
fi

# Add integration to shell config
echo "Installing shell integration..."
echo >> "$RC_FILE"
echo "# Arsenal shell integration (auto-prefill without TIOCSTI)" >> "$RC_FILE"
echo "source \"$INTEGRATION_FILE\"" >> "$RC_FILE"

echo
echo "✅ Installation complete!"
echo
echo "To activate the integration:"
echo "  1. Restart your shell, or"
echo "  2. Run: source $RC_FILE"
echo
echo "Once activated, arsenal will auto-prefill commands without requiring TIOCSTI!"
echo
echo "For $SHELL_NAME:"
if [ "$SHELL_NAME" = "bash" ]; then
    echo "  - Commands will be prefilled using 'read -e -i'"
    echo "  - You can edit the command before executing"
    echo "  - Press Enter to execute, or Ctrl+C to cancel"
elif [ "$SHELL_NAME" = "zsh" ]; then
    echo "  - Commands will be prefilled in your prompt using 'print -z'"
    echo "  - The command appears at your next prompt ready to edit/execute"
fi
echo
echo "=========================================="
