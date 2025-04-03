# Docci | Readme Runner 🚀 &middot; [![GitHub license](https://img.shields.io/badge/license-apache-blue.svg)](https://github.com/Reecepbcups/docci/blob/main/LICENSE) [![Tests](https://github.com/Reecepbcups/docci/actions/workflows/test.yml/badge.svg)](https://github.com/Reecepbcups/docci/actions/workflows/test.yml) [![Compatible](https://img.shields.io/badge/compatible%20-macOS_&_linux-8A2BE2.svg)](https://github.com/Reecepbcups/docci)

Your documentation is now your test suite! 🎯 *(pronounced "doc-ee", short for documentation CI)*

A CI tool that brings your markdown docs to life by executing code blocks in sequence. Run processes in the background, handle environment variables, add delays, verify outputs, and modify files - all through simple markdown tags. Perfect for ensuring your docs stay accurate and your examples actually work! 📚

## 🏃‍♂️ Quick Start

Find sample workspaces in the [`examples/` directory](./examples/).

### 📦 Installation

```bash docci-ignore
make install
```

### 🤖 Github Actions Integration
````yaml
# update the version in the URL
# update the config path argument
- name: Docci Readme Runner
    run: |
    RELEASE=https://github.com/Reecepbcups/docci/releases/download/v0.4.2/docci
    sudo wget -O /usr/local/bin/docci ${RELEASE}
    sudo chmod +x /usr/local/bin/docci
    docci .github/workflows/config.json
````

### 🎮 Usage

```bash docci-ignore
docci <config_path | config_json> [--tags]
# e.g. docci .github/workflows/config.json
# e.g. docci '{"paths": ["docs/README.md"],"working_dir": "docs/","cleanup_cmds": ["kill -9 $(lsof -t -i:3000)"]}'
```

### 🎨 Operation tags
  * 🛑 `docci-ignore`: Skip executing this code block
  * 🔄 `docci-background`: Run the command in the background
  * 🚫 `docci-if-not-installed=BINARY`: Skip execution if some binary is installed (e.g. node)
  * ⏲️ `docci-delay-after=N`: Wait N seconds after running commands
  * ⌛ `docci-delay-per-cmd=N`: Wait N seconds before each command
  * 🌐 `docci-wait-for-endpoint=http://localhost:8080/health|N`: Wait up to N seconds for the endpoint to be ready
  * 📜 `docci-output-contains="string"`: Ensure the output contains a string at the end of the block
  * 🚨 `docci-assert-failure`: If it is expected to fail (non 0 exit code)
  * 🖥️ `docci-os=mac|linux`: Run the command only on it's the specified OS

### 📄 File Tags
  * `docci-file`: The file name to operate on
  * `docci-reset-file`: Reset the file to its original content
  * `docci-if-file-not-exists`: Only run if a file does not exist
  * `docci-line-insert=N`: Insert content at line N
  * `docci-line-replace=N`: Replace content at line N
  * `docci-line-replace=N-M`: Replace content from line N to M

### 💡 Code Block Tag Examples (Operations)

Skip needless installations if you are already set up: 🛑

<!-- The 4 backticks is just so it wraps in githubs UI, real test are written normally with the nested part (just 3 backticks) -->
````bash
```bash docci-os=linux docci-if-not-installed=node
# this only runs if `node` is not found in the system & it's a linux system
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.2/install.sh | bash
export NVM_DIR="$HOME/.nvm"
nvm install v21.7.3
```
````

Ensure the output (stdout or stderr) contains a specific string: 📜

````bash
```bash docci-contains="xyzMyOutput"
echo xyzMyOutput
```
````

Run blocking commands in the background: 🌐

````bash
```bash docci-background
python3 tests/demo.py web-server --port 3000
```
````

Add delays between commands for stability after the endpoint from a previous command is up: ⏱️

````bash
```bash docci-output-contains="GOOD" docci-wait-for-endpoint=http://localhost:3000|30
curl http://localhost:3000/health
```
````

Assert that a command fails: 🚨

````bash
```bash docci-assert-failure
notinstalledbin --version
```
````

Only run a command if a file does not exist: 📄

````bash
```bash docci-if-file-not-exists="README.md" docci-contains-output="ThisLineShouldNeverRun"
# since the file does exist, this line never runs
echo "Output"
```
````

And cleanup demo server if running in the background:

````bash
```bash docci-output-contains="Server shutting down..."
curl http://localhost:3000/kill
```
````

### 💡 Code Block Tag Examples (Files)

Create a new file from content: 📝

<!-- yes, the typo is meant to be here -->
````html
```html docci-file=example.html docci-reset-file
<html>
    <head>
        <title>My Titlee</title>
    </head>
</html>
```
````

Replace the typo'ed line:

````html
```html docci-file=example.html docci-line-replace=3
        <title>My Title</title>
```
````

Add new content

````html
```html docci-file=example.html docci-line-insert=4
    <body>
        <h1>My Header</h1>
        <p>1 paragraph</p>
        <p>2 paragraph</p>
    </body>
```
````

Replace multiple lines

````html
```html docci-file=example.html docci-line-replace=7-9
        <p>First paragraph</p>
        <p>Second paragraph</p>
```
````

## 🛠️ How It Works

The tool processes markdown files and executes code blocks based on configuration settings. The core workflow is handled by several key components:

1. 📋 **Configuration Loading** (`config_types.py`): Loads and validates the JSON configuration file
2. 📝 **Markdown Processing** (`main.py`): Parses markdown files and processes code blocks
3. ⚡ **Command Execution** (`execute.py`): Handles command execution and env vars
4. 🎯 **Tag Processing** (`models.py`): Manages execution control tags

Control how your documentation code blocks are executed with no code, just code block tags. 🏷️

## ⚙️ JSON Configuration Options

- 📂 `paths`: List of markdown files or directories to process (required)
- 🔐 `env_vars`: Environment variables to set during execution
- 🎬 `pre_cmds`: Commands to run before processing markdown
- 🧹 `cleanup_cmds`: Commands to run after processing
- 📂 `working_dir`: Working directory for command execution

### 📝 Config Example

```json
{
  "paths": ["docs/README.md"],
  "env_vars": {
    "NODE_ENV": "test"
  },
  "working_dir": "docs/",
  "debugging": false,
  "pre_cmds": ["npm install"],
  "cleanup_cmds": ["docker-compose down"],
}
```

## 🚧 Limitations

- Multi-line commands in docs are not supported yet
