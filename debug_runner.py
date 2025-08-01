#!/usr/bin/env python3
"""
Debug runner that keeps the debugger session alive.
Run this script to start a debug session, then execute CLI commands interactively.
"""

import subprocess
import sys
from pathlib import Path


def show_help(cli_path: Path, repo_root: Path):
    """Show help by calling the actual CLI help command"""
    print("🐛 Debug session started.")
    print("\n📋 Available commands:")
    subprocess.run([sys.executable, str(cli_path), "--help"], cwd=repo_root)
    print("\n💡 Debug runner commands:")
    print("  help : Show this help again")
    print("  quit : Exit debug session")
    print()


def main():
    repo_root = Path(__file__).parent
    cli_path = repo_root / "src" / "diffmage" / "cli" / "main.py"

    show_help(cli_path, repo_root)

    while True:
        try:
            command = input("diffmage> ").strip()
            if command in ["quit", "exit", "q"]:
                break

            if command in ["help", "h", "--help"]:
                show_help(cli_path, repo_root)
                continue

            if not command:
                continue

            # Run the CLI command
            cmd = [sys.executable, str(cli_path)] + command.split()
            subprocess.run(cmd, cwd=repo_root)

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except EOFError:
            break


if __name__ == "__main__":
    main()
