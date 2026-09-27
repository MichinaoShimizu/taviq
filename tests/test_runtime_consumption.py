import importlib.util, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
P=Path(__file__).parents[1]/"scripts"/"taviq_prepare_commit_msg.py"
S=importlib.util.spec_from_file_location("hook",P); M=importlib.util.module_from_spec(S); S.loader.exec_module(M)
class RuntimeRetentionTests(unittest.TestCase):
    def test_prepare_commit_does_not_delete_runtime(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); runtime=root/".taviq"/"runtime.json"; runtime.parent.mkdir()
            runtime.write_text('{"schema_version":1,"base_head":"abc","tools":["claude","codex"],"modes":["agent"],"models":[]}')
            msg=root/"msg"; msg.write_text("Change\n")
            with patch.object(M,"runtime_path",return_value=runtime):
                result=M.apply(msg,{})
            self.assertTrue(result["applied"])
            self.assertTrue(runtime.exists())
            self.assertIn("Taviq-Tools: claude,codex",msg.read_text())
if __name__=="__main__": unittest.main()
