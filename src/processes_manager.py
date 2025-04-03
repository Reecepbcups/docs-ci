import os
import signal
from typing import Dict

from src.managers.streaming import StreamingProcess


class _ProcessManager:
    """Manages background processes for cleanup."""

    def __init__(self):
        self.background_processes: Dict[int, str] = {}

    def add_process(self, pid: StreamingProcess | int | None, description: str = "") -> None:
        """Add a process ID to the tracked list."""
        if pid is None:
            return
        self.background_processes[pid] = description

    def cleanup(self) -> None:
        """Kill all saved background processes."""
        if not self.background_processes:
            return

        print(f"\nCleaning up {len(self.background_processes)} background processes...")
        pid: int | StreamingProcess
        for pid, description in self.background_processes.items():
            try:
                unique_pid: int
                if isinstance(pid, StreamingProcess):
                    unique_pid = pid.process.pid
                    pid.stop()
                else:
                    unique_pid = pid
                    os.kill(pid, signal.SIGTERM)

                print(f"  [✓] Terminated: {unique_pid=}, {description=}")
            except OSError:
                # Process might have already terminated
                pass

        # Clear the list
        self.background_processes.clear()

# Create a singleton instance for global access
process_manager = _ProcessManager()
