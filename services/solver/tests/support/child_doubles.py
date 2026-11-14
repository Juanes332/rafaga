"""Heavy-lane child doubles (importable by spawned processes)."""

import time
from multiprocessing.queues import Queue
from multiprocessing.synchronize import Event


def sleepy_child(job: dict, settings: dict, progress: Queue, cancel: Event, result: Queue) -> None:
    """Test double: report progress forever and ignore cancellation."""
    while True:
        progress.put((0.1, "spinup", 60))
        time.sleep(0.3)


def polite_child(job: dict, settings: dict, progress: Queue, cancel: Event, result: Queue) -> None:
    """Test double: run until cancelled or for the payload's sleep_s."""
    deadline = time.monotonic() + float(job["payload"].get("sleep_s", 3600))
    while time.monotonic() < deadline:
        if cancel.is_set():
            result.put(("cancelled",))
            return
        progress.put((0.2, "spinup", 10))
        time.sleep(0.2)
    result.put(("error", "internal_error", "test child finished", {}))


def crashing_child(job: dict, settings: dict, progress: Queue, cancel: Event, result: Queue) -> None:
    """Test double: die like a segfaulting kernel (no result posted)."""
    import os

    if job["payload"].get("sleep_s") is not None:
        time.sleep(0.2)
        result.put(("error", "internal_error", "done", {}))
        return
    os._exit(3)


def ok_child(job: dict, settings: dict, progress: Queue, cancel: Event, result: Queue) -> None:
    """Test double: succeed at once with the contract example manifest."""
    from tests.support.contracts import example

    manifest = example("result-manifest.example") | {"dir": job["payload"]["output_dir"]}
    result.put(("ok", manifest))
