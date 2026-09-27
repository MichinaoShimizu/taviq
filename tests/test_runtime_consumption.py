import importlib.util, tempfile, unittest
from pathlib import Path
from unittest.mock import patch

P=Path(__file__).parents[1]/"scripts"/"taviq_prepare_commit_msg.py"
S=importlib.util.spec_from_file_location("hook",P); M=importlib.util.module_from_spec(S); S.loader.exec_module(M)

class RuntimeConsumptionTests(unittest.TestCase):
    def test_successful_commit_consumes_runtime(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); runtime=root/".taviq"/"runtime.json"; runtime.parent.mkdir()
            runtime.write_text('{"tools":["claude","codex"],"modes":["agent"],"models":[]}')
            msg=root/"msg"; msg.write_text("Change\n")
            with patch.object(M,"runtime_path",return_value=runtime):
                r=M.apply(msg,{})
            self.assertTrue(r["applied"])
            self.assertFalse(runtime.exists())
            text=msg.read_text()
            self.assertIn("Taviq-Tools: claude,codex",text)

    def test_existing_trailer_does_not_consume_runtime(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); runtime=root/".taviq"/"runtime.json"; runtime.parent.mkdir()
            runtime.write_text('{"tools":["kiro"],"modes":["agent"],"models":[]}')
            msg=root/"msg"; msg.write_text("Change\n\nTaviq-Provenance: v1\nTaviq-Tools: claude\n")
            with patch.object(M,"runtime_path",return_value=runtime):
                r=M.apply(msg,{})
            self.assertFalse(r["applied"])
            self.assertTrue(runtime.exists())

if __name__=="__main__": unittest.main()
