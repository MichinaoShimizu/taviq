import importlib.util, tempfile, unittest
from pathlib import Path
P=Path(__file__).parents[1]/"scripts"/"taviq_prepare_commit_msg.py"
S=importlib.util.spec_from_file_location("hook",P); M=importlib.util.module_from_spec(S); S.loader.exec_module(M)
class BasicHookTests(unittest.TestCase):
    def test_no_tool_means_no_trailer(self):
        self.assertEqual(M.trailer_lines({}),[])
    def test_minimal_trailer(self):
        self.assertEqual(M.trailer_lines({"TAVIQ_TOOL":"claude"}),["Taviq-Provenance: v1","Taviq-Tool: claude"])
    def test_optional_mode_and_model(self):
        x=M.trailer_lines({"TAVIQ_TOOL":"codex","TAVIQ_MODE":"agent","TAVIQ_MODEL":"model-x"})
        self.assertIn("Taviq-Mode: agent",x); self.assertIn("Taviq-Model: model-x",x)
    def test_invalid_mode_is_omitted(self):
        self.assertNotIn("Taviq-Mode: weird",M.trailer_lines({"TAVIQ_TOOL":"kiro","TAVIQ_MODE":"weird"}))
    def test_apply_is_idempotent(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"msg"; p.write_text("Implement feature\n")
            env={"TAVIQ_TOOL":"claude","TAVIQ_MODE":"agent"}
            self.assertTrue(M.apply(p,env)); self.assertFalse(M.apply(p,env))
            self.assertEqual(p.read_text().count("Taviq-Provenance:"),1)
if __name__=="__main__": unittest.main()
