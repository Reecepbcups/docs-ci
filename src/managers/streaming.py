
# StreamingProcess for background running instances we want to still stream output for
import queue
import threading
import time

import pexpect


# StreamingProcess streams the output from a command in a non blocking way.
class StreamingProcess:
    def __init__(self, command, encoding='utf-8', **spawn_kwargs):
        self.command = command
        self.encoding = encoding
        self.process = None
        self.output_queue = queue.Queue()
        self.read_thread = None  # Separate thread for reading output
        self.consume_thread = None # Separate thread for consuming output
        self.is_running = False
        self.spawn_kwargs = spawn_kwargs # i.e. pass through cwd=

    def start(self) -> "StreamingProcess":
        self.is_running = True
        self.process = pexpect.spawn(self.command, encoding=self.encoding, **self.spawn_kwargs)
        self.read_thread = threading.Thread(target=self._read_output, daemon=True)
        self.read_thread.start()
        return self

    def _read_output(self):
        try:
            while self.is_running:
                try:
                    line = self.process.readline()
                except pexpect.exceptions.EOF:
                    break # Expected when process finishes
                except OSError as e:
                    # Handle "Bad file descriptor" error gracefully, especially after process termination
                    if e.errno == 9:  #errno.EBADF
                        break
                    else:
                        print(f"Unexpected OSError in read_output: {e}")
                        break
                except Exception as e:
                    print(f"Error reading output: {e}")
                    break

                if not line:
                    break  # Process finished or EOF
                self.output_queue.put(line)
        finally:
            self.stop()  # Ensure cleanup

    def attach_consumer(self, consumer_function) -> "StreamingProcess":
         """Attaches a consumer function to process the output in a non blocking way."""
         self.consume_thread = threading.Thread(target=self._consume_output, args=(consumer_function,), daemon=True)
         self.consume_thread.start()
         return self

    @staticmethod
    def output_consumer(line: str):
        """Example consumer function: prints the line to stdout."""
        print(line.strip())

    def _consume_output(self, consumer_function):
        try:
            while self.is_running or not self.output_queue.empty():
                try:
                    line = self.output_queue.get(timeout=1)  # Adjusted timeout
                    if line:
                        consumer_function(line)
                    else:
                        time.sleep(0.1)  # Prevent busy-waiting
                except queue.Empty:
                    # Queue is empty, but the process might still be running, so keep trying
                    pass

        except Exception as e:
            print(f"Error consuming output: {e}")
        finally:
            pass

    def stop(self):
        if self.is_running:
            self.is_running = False
            if self.process:
                try:
                    self.process.close(force=True)  # Terminate the process
                except:
                    pass  # Handle potential errors when closing
