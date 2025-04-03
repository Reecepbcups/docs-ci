# Node Project Example

## Install Node if not already

yes, technically you can just do this in the github action. Showing how you do in a README.md

```bash docci-if-not-installed=node
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.2/install.sh | bash
export NVM_DIR="$HOME/.nvm"
nvm install v21.7.3
```

<!-- TODO: how to persist this within the shell for the duration of the docci run? -->
```bash docci-ignore
cd examples/1-node
```

## Install dependencies

```bash docci-delay-after=1
npm i
```

## Build the Binary

```bash
npx tsc
```

## Run the blocking process in the background

```bash
export SOME_ENV_VAR_PATH="hidden_path"
```

```bash docci-background docci-delay-after=1
EXAMPLE_PORT=3001 node dist/app.js
```

## Test the server output matches expected

```bash docci-output-contains="Hello World!"
curl -X GET http://localhost:${EXAMPLE_PORT} --no-progress-meter
```

```bash docci-output-contains="found!"
curl -X GET http://localhost:${EXAMPLE_PORT}/${SOME_ENV_VAR_PATH} --no-progress-meter
```

## Kill the server after testing

the config.json also handles this, but if you change the port then it would change.

```bash
kill -9 $(lsof -t -i:${EXAMPLE_PORT})
```
