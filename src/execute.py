import os
import re
import sys
from typing import Dict

import pexpect

from src.managers.streaming import StreamingProcess
from src.processes_manager import process_manager


# TODO: add is_debugging
def execute_command(command: str, is_debugging: bool = False, is_background: bool = False, **kwargs) -> tuple[int, str] | pexpect.spawn:
    """Execute a shell command and return its exit status and output."""
    kwargs['env'] = kwargs.get('env', os.environ.copy())

    # assert 'cwd' in kwargs, "execute_command cwd must be provided"
    kwargs['cwd'] = kwargs.get('cwd', os.getcwd())
    if kwargs['cwd'] is None:
        kwargs['cwd'] = os.getcwd()

    # ensure cwd exists, if not error
    if not os.path.exists(kwargs['cwd']):
        raise ValueError(f"cwd {kwargs['cwd']} does not exist")

    # TODO: process if it is an env var and pass through `` and $()

    # if is_debugging:
    print(f"    Executing: {command=} in {kwargs['cwd']=}")

    if not is_background:
        kwargs['withexitstatus'] = True
        result, status = pexpect.run(f'''bash -c "{command}"''', **kwargs)

        if status == 0:
            sys.stdout.buffer.write(result); sys.stdout.flush()
        else:
            sys.stderr.buffer.write(result); sys.stderr.flush()

        decoded = result.decode('utf-8').replace("\r\n", "")
        return status, decoded


    spawn = StreamingProcess(f"{command}", cwd=kwargs['cwd']).start().attach_consumer(StreamingProcess.output_consumer)
    process = spawn.process
    if process.pid:
        process_manager.add_process(spawn, command)
    return process

def execute_substitution_commands(value: str) -> str:
    """
    Execute commands inside backticks or $() and return the value with output substituted.

    Args:
        value: String that may contain backtick or $() commands

    Returns:
        String with commands replaced by their output
    """
    result = value

    # Process all commands
    patterns = [
        (r'`(.*?)`', lambda match: execute_command(match.group(1))),
        (r'\$\((.*?)\)', lambda match: execute_command(match.group(1)))
    ]

    for pattern, handler in patterns:
        # Keep replacing until no more matches
        while True:
            match = re.search(pattern, result)
            if not match:
                break

            full_match = match.group(0)
            replacement = handler(match)
            result = result.replace(full_match, replacement[1]) # returns tuple[int, str] from the execute_command

    return result

def parse_env(command: str) -> Dict[str, str]:
    """
    Parse environment variable commands, handling backtick execution and inline env vars.

    Args:
        command: String containing potential env var assignments and commands

    Returns:
        Dictionary of environment variables (can be empty if no env vars found)
    """
    # Early return if no '=' is present in the command
    if '=' not in command:
        return {}

    # First check for export KEY=VALUE pattern
    export_match = re.match(r'^export\s+([A-Za-z_][A-Za-z0-9_]*)=(.*)$', command.strip())
    if export_match:
        key = export_match.group(1)
        value = execute_substitution_commands(export_match.group(2))
        return {key: value}

    # Check for inline environment variables (KEY=VALUE command args)
    inline_match = re.match(r'^([A-Za-z_][A-Za-z0-9_]*=[^ ]+(?: [A-Za-z_][A-Za-z0-9_]*=[^ ]+)*) (.+)$', command.strip())
    if inline_match:
        env_vars = {}
        env_part = inline_match.group(1)

        # Extract all KEY=VALUE pairs
        for pair in env_part.split():
            if '=' in pair:
                key, value = pair.split('=', 1)
                env_vars[key] = execute_substitution_commands(value)

        return env_vars

    # Check for standalone KEY=VALUE
    standalone_match = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)=(.*)$', command.strip())
    if standalone_match:
        key = standalone_match.group(1)
        value = execute_substitution_commands(standalone_match.group(2))
        return {key: value}

    # If we get here, there were no environment variables we could parse
    return {}
