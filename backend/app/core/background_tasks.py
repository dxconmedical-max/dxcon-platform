import threading
import uuid
from concurrent.futures import ThreadPoolExecutor


class BackgroundTaskRunner:
    def __init__(self, max_workers=4):
        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="dxcon-bg")
        self.submitted = 0
        self.completed = 0
        self.failed = 0
        self.pending = 0

    def submit(self, fn, *args, **kwargs):
        task_id = str(uuid.uuid4())

        def _wrapper():
            try:
                fn(*args, **kwargs)
                with self._lock:
                    self.completed += 1
            except Exception:
                with self._lock:
                    self.failed += 1
                raise
            finally:
                with self._lock:
                    self.pending = max(self.pending - 1, 0)

        with self._lock:
            self.submitted += 1
            self.pending += 1

        self._executor.submit(_wrapper)
        return task_id

    def run_sync(self, fn, *args, **kwargs):
        task_id = str(uuid.uuid4())
        with self._lock:
            self.submitted += 1
            self.pending += 1

        try:
            result = fn(*args, **kwargs)
            with self._lock:
                self.completed += 1
            return task_id, result
        except Exception:
            with self._lock:
                self.failed += 1
            raise
        finally:
            with self._lock:
                self.pending = max(self.pending - 1, 0)

    def shutdown(self, wait=False):
        self._executor.shutdown(wait=wait)

    def snapshot(self):
        with self._lock:
            return {
                "submitted": self.submitted,
                "completed": self.completed,
                "failed": self.failed,
                "pending": self.pending,
            }


background_tasks = BackgroundTaskRunner()
