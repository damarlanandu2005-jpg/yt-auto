"""Timing and resource measurement for benchmark runs."""
from __future__ import annotations

import json
import os
import platform
import resource
import time
from contextlib import contextmanager
from pathlib import Path


class Bench:
    def __init__(self):
        self.stages: dict[str, float] = {}
        self.start = time.perf_counter()
        self.info: dict = {}

    @contextmanager
    def stage(self, name: str):
        t0 = time.perf_counter()
        try:
            yield
        finally:
            self.stages[name] = round(time.perf_counter() - t0, 2)
            print(f"[bench] {name}: {self.stages[name]} s", flush=True)

    def report(self) -> dict:
        self_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        child_kb = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
        return {
            "total_seconds": round(time.perf_counter() - self.start, 2),
            "stages_seconds": self.stages,
            "peak_memory_mb": {"python": round(self_kb / 1024, 1), "largest_child": round(child_kb / 1024, 1)},
            "machine": {
                "arch": platform.machine(),
                "cpus": os.cpu_count(),
                "python": platform.python_version(),
                "runner": os.environ.get("RUNNER_NAME", "local"),
            },
            **self.info,
        }

    def save(self, path: Path) -> dict:
        data = self.report()
        path.write_text(json.dumps(data, indent=2))
        return data
