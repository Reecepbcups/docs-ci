import express from 'express';
const app = express();
const port = process.env.EXAMPLE_PORT || 3000;
const hidden_path = process.env.SOME_ENV_VAR_PATH || "";

app.get('/', (req, res) => {
  res.send('Hello World!');
});

// create a new get endpoint for hidden_path if it is set, if it is, return "found!"
if (hidden_path) {
  app.get(`/${hidden_path}`, (req, res) => {
    res.send('found!');
  });
}

app.listen(port, () => {
  return console.log(`Express is listening at http://localhost:${port}, ${hidden_path}`);
});
