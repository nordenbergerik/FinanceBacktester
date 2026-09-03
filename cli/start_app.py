from __future__ import annotations

import signal
import subprocess
import sys
import time
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


def main() -> None:
    """Start the API and static frontend together."""
    commands = [
        [
            sys.executable,
            "-m",
            "uvicorn",
            "api.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8000",
        ],
        [
            sys.executable,
            "-m",
            "http.server",
            "4173",
            "--bind",
            "127.0.0.1",
            "--directory",
            str(ROOT_DIR / "frontend"),
        ],
    ]
    processes: list[subprocess.Popen[bytes]] = []

    def stop_processes(*_) -> None:
        for process in processes:
            if process.poll() is None:
                process.terminate()
        for process in processes:
            if process.poll() is None:
                process.wait()

    signal.signal(signal.SIGINT, stop_processes)
    signal.signal(signal.SIGTERM, stop_processes)

    try:
        for command in commands:
            processes.append(subprocess.Popen(command, cwd=ROOT_DIR))

        print("Finance Backtester is running:")
        print("  Frontend: http://localhost:4173")
        print("  API:      http://localhost:8000/docs")
        print("Press Ctrl+C to stop both servers.")

        while all(process.poll() is None for process in processes):
            time.sleep(0.25)
    finally:
        stop_processes()


if __name__ == "__main__":
    main()
