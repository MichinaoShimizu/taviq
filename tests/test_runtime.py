import importlib.util, json, tempfile, unittest
from pathlib import Path
P=Path(__file__).parents[1]/"scripts"/"set_runtime.py"
S=importlib.util.spec_from_file_location("rt",P); M=importlib.util.module_from_spec(S); S.loader.exec_module(M)

class RuntimeTests(unittest.TestCase):
    def test_accumulates_tools_modes_models_as_sets(self):
        with tempfile.TemporaryDirectory() as d:
            p=M.write("claude","agent","sonnet",d)
            M.write("codex","agent","gpt-x",d)
            M.write("claude","agent","sonnet",d)
            x=json.loads(p.read_text())
            self.assertEqual(x["tools"],["claude","codex"])
            self.assertEqual(x["modes"],["agent"])
            self.assertEqual(x["models"],["gpt-x","sonnet"])
    def test_model_is_optional(self):
        with tempfile.TemporaryDirectory() as d:
            p=M.write("kiro","agent",None,d)
            x=json.loads(p.read_text())
            self.assertEqual(x["tools"],["kiro"])
            self.assertEqual(x["models"],[])
    def test_invalid_tool_rejected(self):
        with self.assertRaises(ValueError): M.write("other","agent",None,".")

if __name__=="__main__": unittest.main()