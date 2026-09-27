import importlib.util, json, tempfile, unittest
from pathlib import Path
P=Path(__file__).parents[1]/"scripts"/"set_runtime.py"
S=importlib.util.spec_from_file_location("rt",P); M=importlib.util.module_from_spec(S); S.loader.exec_module(M)
class RuntimeTests(unittest.TestCase):
    def test_runtime_contains_only_basic_metadata(self):
        with tempfile.TemporaryDirectory() as d:
            p=M.write("claude","agent","model-x",d)
            x=json.loads(p.read_text())
            self.assertEqual(x,{"tool":"claude","mode":"agent","model":"model-x"})
    def test_unknown_model_can_be_omitted(self):
        with tempfile.TemporaryDirectory() as d:
            p=M.write("codex","agent",None,d)
            self.assertNotIn("model",json.loads(p.read_text()))
    def test_invalid_tool_rejected(self):
        with self.assertRaises(ValueError): M.write("other","agent",None,".")
if __name__=="__main__": unittest.main()
