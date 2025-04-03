import os
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass
from typing import List, Optional, Union

from pexpect import spawn

from src.config import Config
from src.execute import execute_command, parse_env
from src.managers.delay import DelayManager
from src.processes_manager import process_manager


@dataclass
class CommandExecutor:
    commands: List[str]
    background: bool = False
    output_contains: Optional[str] = None
    expect_failure: bool = False
    machine_os: Optional[str] = None
    binary: Optional[str] = None
    ignored: bool = False
    delay_manager: Optional[DelayManager] = None
    if_file_not_exists: str = ""

    def run_commands(
        self,
        config: Config,
        background_exclude_commands: List[str] = ["cp", "export", "cd", "mkdir", "echo", "cat"], # TODO: remove?
    ) -> str | None:
        if skip_reason := self._should_skip_codeblock_execution(config):
            return None

        response = None
        had_error = False

        for command in self.commands:
            if self._should_skip_cmd_execution(config, command):
                continue

            # Update global environment (and persist through the future codeblock sections on this test)
            # _execute_command will load in this
            envs = parse_env(command)
            print(f"    ENVS: {envs} for {command=}")
            os.environ.update(envs)

            cmd_background = self._should_run_in_background(command, background_exclude_commands)

            if config.debugging:
                print(f"Running: {command=}, {cmd_background=}")

            # Handle pre-execution delay if set
            if self.delay_manager:
                self.delay_manager.handle_delay("cmd")

            # Execute command and handle result
            # this passes the os.environ copy due to working with multiple threads
            result = self._execute_command(command, config, cmd_background, env=os.environ.copy())
            if isinstance(result, str):
                response = result
                break
            elif result is True:  # Had error
                had_error = True

        if self.delay_manager:
            self.delay_manager.handle_delay("post")

        if self.expect_failure:
            if had_error:
                return None
            else:
                return "Error: expected failure but command succeeded"

        return response

    def _execute_command(self, command: str, config: Config, cmd_background: bool, env: dict) -> Union[str, bool, None]:
        """
        Execute a command and handle its output.
        Returns:
            - str: Error message if command failed
            - True: If stderr had output (error occurred)
            - None: If command executed successfully
        """
        tmp = execute_command(command, is_background=cmd_background, is_debugging=config.debugging, cwd=config.working_dir, env=env)

        # already handled in execute_command to run a background process thread
        if cmd_background:
            # process: spawn = tmp
            return None

        status: int | None = tmp[0]
        output: str = tmp[1]


        if self.output_contains:
            # Only check output contains if this is the last non-empty command
            non_empty_commands = [cmd for cmd in self.commands if cmd.strip() and not cmd.strip().startswith('#')]
            if non_empty_commands and command == non_empty_commands[-1]:
                if self.output_contains not in output:
                    return f"Error: `{self.output_contains}` is not found in output, output: {output} for {command}"
                elif config.debugging:
                    print(f"Output contains: {self.output_contains}")
        else:
            if status is None:
                return None

            if status != 0:
                return f"Error ({status=}) {command=}"

        return None

    def _should_skip_codeblock_execution(self, config: Config) -> bool:
        """Check various conditions that would cause us to skip command execution."""
        # Skip if marked as ignored
        if self.ignored:
            if config.debugging:
                print(f"Ignoring commands... ({self.commands}))")
            return True

        # Skip if target file already exists
        if self.if_file_not_exists:
            file_path = os.path.join(config.working_dir, self.if_file_not_exists) if config.working_dir else self.if_file_not_exists
            if os.path.exists(file_path):
                if config.debugging:
                    print(f"Skipping commands since {file_path} exists")
                return True

        # Skip if OS doesn't match
        system = platform.system().lower()
        if self.machine_os and self.machine_os != system:
            if config.debugging:
                print(f"Skipping command since it is not for the current OS: {self.machine_os}, current: {system}")
            return True

        # Skip if binary is already installed
        if self.binary and shutil.which(self.binary):
            print(f"Skipping command since {self.binary} is already installed.")
            return True

        return False

    def _should_skip_cmd_execution(self, config:Config, command: str) -> bool:
        # Skip empty commands and comments
        if not command.strip() or command.strip().startswith('#'):
            return True

        if command in config.ignore_commands:
            return True
        return False

    def _should_run_in_background(self, command: str, exclude_commands: List[str]) -> bool:
        if not self.background:
            return False
        first_word = command.strip().split()[0]
        return first_word not in exclude_commands
