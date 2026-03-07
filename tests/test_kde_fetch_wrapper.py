import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "com.aiusagemonitor" / "contents" / "scripts" / "fetch_all_usage.py"
SPEC = importlib.util.spec_from_file_location("kde_fetch_wrapper", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class KDEFetchWrapperTests(unittest.TestCase):
    def test_candidate_roots_prefers_bundled_vendor_first(self):
        fake = Path("/tmp/repo/com.aiusagemonitor/contents/scripts/fetch_all_usage.py")
        roots = MODULE.candidate_roots(fake)

        self.assertEqual(roots[0], Path("/tmp/repo/com.aiusagemonitor/contents/vendor"))
        self.assertEqual(roots[1], Path("/tmp/repo"))

    def test_extend_sys_path_accepts_bundled_core(self):
        with tempfile.TemporaryDirectory() as tmp:
            temp_root = Path(tmp)
            script_path = temp_root / "com.aiusagemonitor" / "contents" / "scripts" / "fetch_all_usage.py"
            bundled_core = temp_root / "com.aiusagemonitor" / "contents" / "vendor" / "core" / "ai_usage_monitor"
            bundled_core.mkdir(parents=True)

            original_sys_path = list(sys.path)
            try:
                MODULE.extend_sys_path(script_path)
                self.assertIn(str(temp_root / "com.aiusagemonitor" / "contents" / "vendor"), sys.path)
            finally:
                sys.path[:] = original_sys_path


if __name__ == "__main__":
    unittest.main()
