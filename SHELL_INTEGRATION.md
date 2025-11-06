# Arsenal Shell Integration Guide

## The Problem

Modern Linux kernels (6.2+) disable `TIOCSTI` for security reasons, breaking Arsenal's command auto-prefill feature. Without TIOCSTI, Arsenal cannot inject commands into your terminal input buffer.

## The Solution

We've implemented **shell integration** that provides true auto-prefill without requiring TIOCSTI!

## Quick Installation

Run the installer:
```bash
./install.sh
```

Then restart your shell or run:
```bash
source ~/.bashrc  # for bash
source ~/.zshrc   # for zsh
```

## Manual Installation

Add this line to your shell config file:

**Bash** (`~/.bashrc`):
```bash
source /path/to/arsenal/arsenal_shell_integration.sh
```

**Zsh** (`~/.zshrc`):
```bash
source /path/to/arsenal/arsenal_shell_integration.sh
```

## How It Works

### For Bash Users
- Uses `read -e -i` to prefill commands
- After selecting a command in Arsenal, you'll see an interactive prompt with the command pre-filled
- You can:
  - Press **Enter** to execute as-is
  - **Edit** the command before executing
  - Press **Ctrl+C** to cancel
- Commands are automatically added to bash history

### For Zsh Users
- Uses `print -z` to push commands to the buffer stack
- After selecting a command in Arsenal, it will appear in your next prompt
- You can:
  - Press **Enter** to execute as-is
  - **Edit** the command before executing
  - **Clear** the line if you don't want to execute
- The command appears just like you typed it

## Fallback Methods

If you don't install shell integration, Arsenal will automatically try:

1. **TIOCSTI** - Works on old kernels (automatic)
2. **Clipboard** - Copies to system clipboard (requires `pyperclip`)
3. **OSC 52** - Copies via terminal escape codes
4. **Print** - Simply displays the command

## Comparison

| Method | Auto-Prefill | Edit Before Execute | In History | Works on Modern Kernels |
|--------|--------------|---------------------|------------|-------------------------|
| TIOCSTI (old) | ✅ | ✅ | ✅ | ❌ Disabled |
| Shell Integration | ✅ | ✅ | ✅ | ✅ Works! |
| Clipboard | ❌ Manual paste | ✅ | ✅ | ✅ |
| Print | ❌ Manual copy | ✅ | ✅ | ✅ |

## Command-Line Options

You can still use Arsenal's command-line options:

```bash
arsenal           # Default behavior (uses shell integration if installed)
arsenal --copy    # Force clipboard mode
arsenal --exec    # Execute immediately (no edit)
arsenal --tmux    # Send to tmux pane
arsenal --print   # Just print the command
```

## Troubleshooting

### "Command not prefilled"
- Make sure you sourced the integration file
- Check that `$ARSENAL_SHELL_INTEGRATION` is set:
  ```bash
  echo $ARSENAL_SHELL_INTEGRATION  # Should output: 1
  ```

### Bash: "Command ready" but nothing happens
- Requires Bash 4.0 or later
- Check your version: `echo $BASH_VERSION`
- Upgrade bash if needed

### Zsh: Command appears as text instead of in prompt
- This is expected behavior for some terminals
- The command should still appear at your next prompt

### Shell integration not working
- Make sure you're using bash or zsh
- Try the fallback modes (`--copy`, `--exec`, `--print`)

## Benefits

✅ **True auto-prefill** - Commands appear ready to execute
✅ **Edit before execute** - Modify commands as needed
✅ **History integration** - Commands saved in shell history
✅ **No kernel changes** - Works on modern kernels
✅ **No sudo required** - User-space solution
✅ **Shell-aware** - Uses native shell features

## Technical Details

### Bash Implementation
- Wrapper function intercepts arsenal calls
- Reads command from `~/.arsenal_cmd` file
- Uses `read -e -i "$cmd"` to prefill readline
- Executes with `eval` and adds to history with `history -s`

### Zsh Implementation
- Wrapper function intercepts arsenal calls
- Reads command from `~/.arsenal_cmd` file
- Uses `print -z "$cmd"` to push to buffer stack
- Next prompt automatically shows the command

## Support

- **Supported Shells**: Bash 4.0+, Zsh
- **Tested On**: Linux (Debian, Ubuntu, Arch, Kali)
- **Issue Tracker**: https://github.com/Orange-Cyberdefense/arsenal/issues/77

## Credits

This solution was developed to address GitHub issue #77 regarding TIOCSTI being disabled in modern Linux kernels. The shell integration approach provides a user-friendly alternative that works on all modern systems without requiring kernel modifications or sudo access.
