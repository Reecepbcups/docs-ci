


import os
import threading
import time
import unittest

from config import Config
from execute import execute_substitution_commands
from main import (
    DocsValue,
    Tags,
    parse_env,
    parse_markdown_code_blocks,
    run_documentation,
)
from models import Endpoint
from tests.test_server import MyServer

curr_dir = os.path.dirname(os.path.abspath(__file__))


class TestSomething(unittest.TestCase):
    def test_process_language_parts(self):
        dv = parse_markdown_code_blocks(config=None, content='```bash docci-output-contains="My Multi Word Value"\npython3 example.py```')[0]
        self.assertEqual(dv.command_executor.output_contains, "My Multi Word Value")

        dv = parse_markdown_code_blocks(config=None, content='```bash docci-output-contains="My Multi Word Value" docci-delay-after=123\npython3 example.py```')[0]
        self.assertEqual(dv.command_executor.output_contains, "My Multi Word Value")
        self.assertEqual(dv.delay_manager.post_delay, 123)


    def test_extract_tag_value(self):
        # this is after process_language_parts, we just input good values here for verification
        resp = Tags.extract_tag_value(tags=['docci-output-contains="My Value"'], tag_type=Tags.OUTPUT_CONTAINS(), default=None)
        self.assertEqual(resp, "My Value")
        resp = Tags.extract_tag_value(tags=['docci-delay-after=123'], tag_type=Tags.POST_DELAY(), default=None, converter=int)
        self.assertEqual(resp, 123)
        resp = Tags.extract_tag_value(tags=['docci-file=proto/example/example.proto'], tag_type=Tags.FILE_NAME(), default=None)
        self.assertEqual(resp, "proto/example/example.proto")

    def test_config_run_1(self):
        err = run_documentation(Config.load_from_file(os.path.join(curr_dir, "config1.json")))
        self.assertEqual(err, None, err)

    def test_multiple_paths_same_output(self):
        # if you use multiple paths here, you HAVE to have the same outputs to actually verify. Good for duplicate documentation places that should match up exactly
        err = run_documentation(Config.from_json({"paths":["tests/README1.md", "tests/README2.md"],"env_vars": {},"pre_cmds": [],"cleanup_cmds": []}))
        self.assertEqual(err, None, err)

    def test_execute_substitution_commands(self):
        # nothing to exec, leave as is
        self.assertEqual(execute_substitution_commands('123'), '123')
        # exec's within the backticks and performs the substitution
        self.assertEqual(execute_substitution_commands('SOME_VAR=`echo 123`'), 'SOME_VAR=123')
        self.assertEqual(execute_substitution_commands('SOME_VAR=`echo 123`'), 'SOME_VAR=123')
        self.assertEqual(execute_substitution_commands('SOME_VAR=$(echo 123)'), 'SOME_VAR=123')
        # double nested
        self.assertEqual(execute_substitution_commands('SOME_VAR=`echo $(echo 123)`'), 'SOME_VAR=123')
        self.assertEqual(execute_substitution_commands('SOME_VAR=$(echo `echo 123`)'), 'SOME_VAR=123')

    def test_parse_env(self):
        self.assertEqual(parse_env('export MY_VARIABLE=`echo 123`'), {'MY_VARIABLE': '123'})
        self.assertEqual(parse_env('export MY_OTHER_VAR=hello'), {'MY_OTHER_VAR': 'hello'})
        self.assertEqual(parse_env('SERVICE_CONFIG_FILE=service_config.json make deploy-service'), {'SERVICE_CONFIG_FILE': 'service_config.json'})

    def test_parse_markdown_code_blocks(self):
        # basic
        dv: DocsValue = parse_markdown_code_blocks(config=None, content='```bash\nexport MY_VARIABLE=`echo 123`\n```')[0]
        self.assertEqual(dv.language, 'bash')
        self.assertEqual(dv.tags, [])
        self.assertEqual(dv.content, 'export MY_VARIABLE=`echo 123`')
        self.assertEqual(dv.command_executor.commands, ['export MY_VARIABLE=`echo 123`'])
        self.assertEqual(dv.command_executor.background, False)
        self.assertEqual(dv.delay_manager.post_delay, 0)
        self.assertEqual(dv.delay_manager.cmd_delay, 0)

        # ignore block
        dv: DocsValue = parse_markdown_code_blocks(config=None, content='# header\nhere is some text\n\n```bash docci-ignore\nexport MY_VARIABLE=`echo 123`\n```')[0]
        self.assertEqual(dv.ignored, True)
        self.assertEqual(dv.tags, [Tags.IGNORE()])

        # multiple tags
        dv: DocsValue = parse_markdown_code_blocks(config=None, content='''# header
                here is some text\n\n
                ```bash docci-delay-after=5 docci-delay-per-cmd=1
                    export MY_VARIABLE=`echo 123`
                    echo 12345
                ```
                other more text `echo example`
                ## section 2
        ''')[0]
        self.assertEqual(dv.ignored, False)
        self.assertEqual(dv.tags, [f"{Tags.POST_DELAY()}=5",f"{Tags.CMD_DELAY()}=1"])

    def test_http_polling_failure_then_success_when_up(self):
        port = MyServer.get_free_port()

        dv: DocsValue = parse_markdown_code_blocks(config=None, content=f'```bash docci-wait-for-endpoint=http://localhost:{port}|30\nexport MY_VARIABLE=`echo 123`\n```')[0]
        self.assertEqual(dv.endpoint, Endpoint(url=f'http://localhost:{port}', max_timeout=30))
        self.assertEqual(dv.tags, [f"{Tags.HTTP_POLLING()}=http://localhost:{port}|30"])

        # server is off, always returns False for now
        returnValues = {}
        for idx, res in enumerate(dv.endpoint.poll(poll_speed=0.1)):
            if idx == 0:
                # server is off
                self.assertFalse(res[0])

            # start the server since the first false came in & we know it is down
            if idx == 1:
                s = MyServer(port)
                server_thread = threading.Thread(target=s.start_server)
                server_thread.start()

            returnValues[res[0]] = res[1]

        # len of returnValues should be 2, since we have 2 yields (1 good & 1 bad)
        self.assertEqual(len(returnValues), 2)

        s.shutdown()
        server_thread.join()

    def test_http_polling_max_timeout(self):
        port = MyServer.get_free_port()

        max_timeout = 2
        dv: DocsValue = parse_markdown_code_blocks(config=None, content=f'```bash docci-wait-for-endpoint=http://localhost:{port}|{max_timeout}\nexport MY_VARIABLE=`echo 123`\n```')[0]
        self.assertEqual(dv.endpoint, Endpoint(url=f'http://localhost:{port}', max_timeout=max_timeout))

        startTime = time.time()
        for res in dv.endpoint.poll(poll_speed=0.1):
            self.assertFalse(res[0])
            # always less than max timeout (reason for little added buffer here)
            self.assertTrue(time.time() - startTime < max_timeout+0.5, f"Time exceeded {max_timeout} seconds")

