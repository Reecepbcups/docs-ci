import os
import re
import time

import pexpect


# execute_substitution_commands  is from execute.py
def execute_substitution_commands(value: str, **kwargs) -> str:
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
        (r'`(.*?)`', lambda match: execute_command(match.group(1), **kwargs)),
        (r'\$\((.*?)\)', lambda match: execute_command(match.group(1), **kwargs))
    ]

    for pattern, handler in patterns:
        # Keep replacing until no more matches
        while True:
            match = re.search(pattern, result)
            if not match:
                break

            full_match = match.group(0)
            replacement = handler(match)
            result = result.replace(full_match, replacement[1]) # TODO: I just change this to grab from the tuple from the output (since status is returned in index 0)

    return result




def execute_command(command: str, is_debugging: bool = False, is_background: bool = False, **kwargs) -> tuple[int, str] | pexpect.spawn:
    """Execute a shell command and return its exit status and output."""
    kwargs['env'] = kwargs.get('env', os.environ.copy())
    kwargs['withexitstatus'] = True

    assert 'cwd' in kwargs, "execute_command cwd must be provided"

    # ensure cwd exists, if not error
    if not os.path.exists(kwargs['cwd']):
        raise ValueError(f"cwd {kwargs['cwd']} does not exist")

    # TODO: process if it is an env var and pass through `` and $()

    # if is_debugging:
    print(f"    Executing {command=} in {kwargs['cwd']=}")

    if not is_background:
        result, status = pexpect.run(f'''bash -c "{command}"''', **kwargs)
        return status, result.decode('utf-8').replace("\r\n", "")

    kwargs.pop('withexitstatus')
    # f = open(os.path.join(kwargs['cwd'], "logfile.txt"), "wb")
    spawn = pexpect.spawn(f"{command}", **kwargs)
    # TODO: cleanup PID later
    return spawn

status, res = execute_command("echo 12345", is_debugging=True, cwd=os.getcwd())
print(status, res)

# repo_root = os.popen("git rev-parse --show-toplevel").read().strip()
# node_ex_dir = os.path.join(repo_root, "examples", "1-node") ## ensures another cwd exists and works

# spawn = execute_command("ping 8.8.8.8", is_debugging=True, cwd=repo_root, is_background=True)
# print(spawn.pid)

# set env variable DEPLOYER_PRIV_KEY to `DEPLOYER_PRIV_KEY=0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80`
os.environ['DEPLOYER_PRIV_KEY'] = '0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80'

# working input example
print(execute_command('echo "12345678" | ondod keys unsafe-import-eth-key test-deploy-acc ${DEPLOYER_PRIV_KEY} --keyring-backend test', is_debugging=True, cwd=os.getcwd()))
print(execute_command('ondod keys delete test-deploy-acc <<< "Y"', is_debugging=True, cwd=os.getcwd()))

# streaming_process = StreamingProcess("ondod start").start().attach_consumer(StreamingProcess.output_consumer)

# PRIV_KEY=2C5F0E00617B6849F8EFD5D74DB1D06D7E516A8B6FF86F6059B024B22D5EACCF
ENV_SET=execute_substitution_commands('PRIV_KEY=`ondod keys unsafe-export-eth-key acc0`', cwd=os.getcwd())

# now take this, parse, and set the os env vars
k, v = ENV_SET.split("=")
os.environ.update({k: v})

print(execute_command('echo hello ${PRIV_KEY}', cwd=os.getcwd())[1])

print(execute_command('EXAMPLE_PORT=3001 node dist/app.js', cwd='/home/reece/Desktop/Programming/Docs/docci/examples/1-node')[1])

time.sleep(1)

# streaming_process = StreamingProcess("ping -n -i 0.1 8.8.8.8").start().attach_consumer(StreamingProcess.output_consumer)


# for i in range(6):
#     print(i); time.sleep(1)

# streaming_process.stop()
