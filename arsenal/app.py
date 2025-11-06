import argparse
import json
import os
import fcntl
import termios
import re
import time
from curses import wrapper

# arsenal
from . import __version__
from .modules import config
from .modules import cheat
from .modules import check
from .modules import gui as arsenal_gui


class App:

    def __init__(self):
        pass

    def get_args(self):
        examples = '''examples:
        arsenal
        arsenal --copy
        arsenal --print

        You can manage global variables with:
        >set GLOBALVAR1=<value>
        >show
        >clear

        (cmd starting with '>' are internals cmd)
        '''

        parser = argparse.ArgumentParser(
            prog="arsenal",
            description='arsenal v{} - Pentest command launcher'.format(__version__),
            epilog=examples,
            formatter_class=argparse.RawTextHelpFormatter
        )

        group_out = parser.add_argument_group('output [default = prefill]')
        group_out.add_argument('-p', '--print', action='store_true', help='Print the result')
        group_out.add_argument('-o', '--outfile', action='store', help='Output to file')
        group_out.add_argument('-x', '--copy', action='store_true', help='Output to clipboard')
        group_out.add_argument('-e', '--exec', action='store_true', help='Execute cmd')
        group_out.add_argument('-t', '--tmux', action='store_true', help='Send command to tmux panel')
        group_out.add_argument('-c', '--check', action='store_true', help='Check the existing commands')
        group_out.add_argument('-f', '--prefix', action='store_true', help='command prefix')
        group_out.add_argument('--no-tags', action='store_false', help='Whether or not to show the'
                                                                       ' tags when drawing the cheats')
        parser.add_argument('-V', '--version', action='version', version='%(prog)s (version {})'.format(__version__))

        return parser.parse_args()

    def run(self):
        args = self.get_args()

        # load cheatsheets
        cheatsheets = cheat.Cheats().read_files(config.CHEATS_PATHS, config.FORMATS,
                                                config.EXCLUDE_LIST)

        if args.check:
            check.check(cheatsheets)
        else:
            self.start(args, cheatsheets)

    def start(self, args, cheatsheets):
        arsenal_gui.Gui.with_tags = args.no_tags

        # create gui object
        gui = arsenal_gui.Gui()
        while True:
            # launch gui
            cmd = gui.run(cheatsheets, args.prefix)

            if cmd == None:
                exit(0)

            # Internal CMD
            elif cmd.cmdline[0] == '>':
                if cmd.cmdline == ">exit":
                    break
                elif cmd.cmdline == ">show":
                    if (os.path.exists(config.savevarfile)):
                        with open(config.savevarfile, 'r') as f:
                            arsenalGlobalVars = json.load(f)
                            for k, v in arsenalGlobalVars.items():
                                print(k + "=" + v)
                    break
                elif cmd.cmdline == ">clear":
                    with open(config.savevarfile, "w") as f:
                        f.write(json.dumps({}))
                    self.run()
                elif re.match(r"^\>set( [^= ]+=[^= ]+)+$", cmd.cmdline):
                    # Load previous global var
                    if (os.path.exists(config.savevarfile)):
                        with open(config.savevarfile, 'r') as f:
                            arsenalGlobalVars = json.load(f)
                    else:
                        arsenalGlobalVars = {}
                    # Add new glovar var
                    varlist = re.findall("([^= ]+)=([^= ]+)", cmd.cmdline)
                    for v in varlist:
                        arsenalGlobalVars[v[0]] = v[1]
                    with open(config.savevarfile, "w") as f:
                        f.write(json.dumps(arsenalGlobalVars))
                else:
                    print("Arsenal: invalid internal command..")
                    break

            # OPT: Copy CMD to clipboard
            elif args.copy:
                try:
                    import pyperclip
                    pyperclip.copy(cmd.cmdline)
                except ImportError:
                    pass
                break

            # OPT: Only print CMD
            elif args.print:
                print(cmd.cmdline)
                break

            # OPT: Write in file
            elif args.outfile:
                with open(args.outfile, 'w') as f:
                    f.write(cmd.cmdline)
                break

            # OPT: Exec
            elif args.exec and not args.tmux:
                os.system(cmd.cmdline)
                break

            elif args.tmux:
                try:
                    import libtmux
                    try:
                        server = libtmux.Server()
                        session = server.list_sessions()[-1]
                        window = session.attached_window
                        panes = window.panes
                        if len(panes) == 1:
                            # split window to get more pane
                            pane = window.split_window(attach=False)
                            time.sleep(0.3)
                        else:
                            pane = panes[-1]
                        # send command to other pane and switch pane
                        if args.exec:
                            pane.send_keys(cmd.cmdline)
                        else:
                            pane.send_keys(cmd.cmdline, enter=False)
                            pane.select_pane()
                    except libtmux.exc.LibTmuxException:
                        self.prefil_shell_cmd(cmd)
                        break
                except ImportError:
                    self.prefil_shell_cmd(cmd)
                    break
            # DEFAULT: Prefill Shell CMD
            else:
                self.prefil_shell_cmd(cmd)
                break

    def prefil_shell_cmd(self, cmd):
        """
        Prefill shell command line using various methods.
        Tries multiple approaches as TIOCSTI is disabled in modern kernels.
        """
        # Method 1: Try TIOCSTI first (legacy method, works on old kernels)
        stdin = 0
        tiocsti_worked = False
        try:
            # Check if we have a TTY first
            if not os.isatty(stdin):
                raise OSError("Not a TTY")

            # save TTY attribute for stdin
            oldattr = termios.tcgetattr(stdin)
            # create new attributes to fake input
            newattr = termios.tcgetattr(stdin)
            # disable echo in stdin -> only inject cmd in stdin queue (with TIOCSTI)
            newattr[3] &= ~termios.ECHO
            # enable non canonical mode -> ignore special editing characters
            newattr[3] &= ~termios.ICANON
            # use the new attributes
            termios.tcsetattr(stdin, termios.TCSANOW, newattr)
            # write the selected command in stdin queue
            for c in cmd.cmdline:
                fcntl.ioctl(stdin, termios.TIOCSTI, c)
            # restore TTY attribute for stdin
            termios.tcsetattr(stdin, termios.TCSADRAIN, oldattr)
            tiocsti_worked = True
            return
        except (OSError, termios.error):
            # TIOCSTI failed - could be modern kernel with security patch or not a TTY
            # Restore terminal on error
            try:
                termios.tcsetattr(stdin, termios.TCSADRAIN, oldattr)
            except:
                pass

        # Method 2: Shell integration - exec into shell with prefill
        if not tiocsti_worked:
            if self._try_shell_integration_prefill(cmd.cmdline):
                return

        # Method 3: Try pyperclip (system clipboard)
        clipboard_worked = False
        try:
            import pyperclip
            pyperclip.copy(cmd.cmdline)
            clipboard_worked = True
            print(f"\n╭{'─' * 78}╮")
            print(f"│ [Arsenal] Command copied to clipboard{' ' * 39}│")
            print(f"│{' ' * 78}│")
            print(f"│ {cmd.cmdline:<76} │")
            print(f"│{' ' * 78}│")
            print(f"│ → Paste with: Ctrl+Shift+V or Middle-click{' ' * 32}│")
            print(f"╰{'─' * 78}╯")
            return
        except (ImportError, Exception) as e:
            pass

        # Method 4: Try OSC 52 (terminal escape sequence clipboard)
        if not clipboard_worked:
            try:
                import base64
                b64_cmd = base64.b64encode(cmd.cmdline.encode()).decode()
                # OSC 52 escape sequence to set clipboard (works in many modern terminals)
                osc52 = f"\033]52;c;{b64_cmd}\007"
                print(osc52, end='', flush=True)
                print(f"\n╭{'─' * 78}╮")
                print(f"│ [Arsenal] Command sent to terminal clipboard{' ' * 32}│")
                print(f"│{' ' * 78}│")
                print(f"│ {cmd.cmdline:<76} │")
                print(f"│{' ' * 78}│")
                print(f"│ → Paste with: Ctrl+Shift+V or Middle-click{' ' * 32}│")
                print(f"╰{'─' * 78}╯")
                return
            except Exception:
                pass

        # Fallback: Just print the command with helpful instructions
        print(f"\n╭{'─' * 78}╮")
        print(f"│ [Arsenal] Auto-prefill not available (TIOCSTI disabled){' ' * 24}│")
        print(f"│{' ' * 78}│")
        print(f"│ Your command:{' ' * 64}│")
        print(f"│ {cmd.cmdline:<76} │")
        print(f"│{' ' * 78}│")
        print(f"│ → Copy and paste manually, or use these options:{' ' * 28}│")
        print(f"│   • arsenal --copy     (auto-copy to clipboard){' ' * 29}│")
        print(f"│   • arsenal --exec     (execute immediately){' ' * 33}│")
        print(f"│   • arsenal --tmux     (send to tmux pane){' ' * 35}│")
        print(f"╰{'─' * 78}╯\n")

    def _try_shell_integration_prefill(self, command):
        """
        Try to prefill command using shell-specific integration via wrapper function.
        Writes command to a temp file that a wrapper function can read.
        """
        import tempfile

        # Check if user has shell integration installed
        if not os.environ.get('ARSENAL_SHELL_INTEGRATION'):
            return False

        # Detect parent shell
        shell = os.environ.get('SHELL', '/bin/bash')
        shell_name = os.path.basename(shell)

        # Write command to the designated file
        arsenal_cmd_file = os.path.expanduser('~/.arsenal_cmd')
        try:
            with open(arsenal_cmd_file, 'w') as f:
                f.write(command)
            # Silently return - the wrapper function will print the message
            return True
        except Exception:
            return False


def main():
    try:
        App().run()
    except KeyboardInterrupt:
        exit(0)


if __name__ == "__main__":
    wrapper(main()) 
