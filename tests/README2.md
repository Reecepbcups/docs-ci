# testing

this is a duplicate of the ../README1.md file to simulate

```
this is ignored
```

```bash docci-output-contains="xyzMyOutput"
echo xyzMyOutput
```

```bash docci-output-contains="abcMyOutput"
echo abcMyOutput
```

```bash docci-output-contains="testingPipedData"
echo "testingPipedData" | echo "$(cat)"
```

```bash docci-output-contains="Valid Output"
printf 'Valid Output'
```

```bash docci-output-contains="Valid Output2"
echo 'Valid Output2'
```

```bash docci-output-contains="TestInputEcho"
read -r input_variable <<< "TestInputEcho"; echo "$input_variable"
```

```bash docci-assert-failure docci-output-contains="NOT THE RIGHT OUTPUT"
echo abcMyOutput
```
