import os
import stat
import tempfile
import unittest
from unittest import mock

from core.ai_usage_monitor.runtime_cache import (
    load_runtime_cache,
    save_runtime_cache,
)


class RuntimeCacheTests(unittest.TestCase):
    def test_save_runtime_cache_persists_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.dict(
                os.environ,
                {"AI_USAGE_MONITOR_STATE_DIR": tmp},
                clear=False,
            ):
                save_runtime_cache("state.json", {"k": "v"})
                loaded = load_runtime_cache("state.json")
        self.assertEqual(loaded, {"k": "v"})

    def test_save_runtime_cache_sets_private_permissions(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.dict(
                os.environ,
                {"AI_USAGE_MONITOR_STATE_DIR": tmp},
                clear=False,
            ):
                save_runtime_cache("state.json", {"k": "v"})
                path = os.path.join(tmp, "state.json")
                mode = stat.S_IMODE(os.stat(path).st_mode)
        self.assertEqual(mode, 0o600)


if __name__ == "__main__":
    unittest.main()
