import importlib.util, json, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
P=Path(__file__).parents[1]/"scripts"/"set_runtime.py"
S=importlib.util.spec_from_file_location("rt",P); M=importlib.util.module_from_spec(S); S.loader.exec_module(M)

class RuntimeTests(unittest.TestCase):
    def test_same_head_accumulates_multiple_tools(self):
        with tempfile.TemporaryDirectory() as d, patch.object(M,"head",return_value="abc"):
            p=M.write("claude","agent","sonnet",d)
            M.write("codex","agent","gpt-x",d)
            x=json.loads(p.read_text())
            self.assertEqual(x["base_head"],"abc")
            self.assertEqual(x["tools"],["claude","codex"])
            self.assertEqual(x["models"],["gpt-x","sonnet"])

    def test_new_head_starts_new_window(self):
        with tempfile.TemporaryDirectory() as d:
            with patch.object(M,"head",return_value="abc"):
                p=M.write("claude","agent","sonnet",d)
            with patch.object(M,"head",return_value="def"):
                M.write("kiro","agent",None,d)
            x=json.loads(p.read_text())
            self.assertEqual(x["base_head"],"def")
            self.assertEqual(x["tools"],["kiro"])
            self.assertEqual(x["models"],[])

    def test_duplicate_observations_are_deduplicated(self):
        with tempfile.TemporaryDirectory() as d, patch.object(M,"head",return_value="abc"):
            p=M.write("claude","agent","sonnet",d)
            M.write("claude","agent","sonnet",d)
            x=json.loads(p.read_text())
            self.assertEqual(x["tools"],["claude"])
            self.assertEqual(x["models"],["sonnet"])

    def test_invalid_tool_rejected(self):
        with self.assertRaises(ValueError): M.write("other","agent",None,".")

if __name__=="__main__": unittest.main()
