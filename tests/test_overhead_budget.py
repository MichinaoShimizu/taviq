import importlib.util, tempfile, unittest
from pathlib import Path
P=Path(__file__).parents[1]/"scripts"/"taviq_prepare_commit_msg.py"
S=importlib.util.spec_from_file_location("hook",P); M=importlib.util.module_from_spec(S); S.loader.exec_module(M)

class OverheadBudgetTests(unittest.TestCase):
    def test_basic_hook_stays_inside_metadata_budget(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"msg"; p.write_text("Benchmark commit\n")
            r=M.apply(p,{"TAVIQ_TOOL":"claude","TAVIQ_MODE":"agent"})
            self.assertTrue(r["applied"])
            self.assertLess(r["metadata_bytes"],1024)

    def test_basic_hook_has_no_ai_dependency(self):
        # The deterministic hook accepts local metadata and writes a trailer.
        # No AI client, API key, token counter, or network dependency is involved.
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"msg"; p.write_text("Offline commit\n")
            r=M.apply(p,{"TAVIQ_TOOL":"kiro","TAVIQ_MODE":"agent"})
            self.assertTrue(r["applied"])
            self.assertIn("Taviq-Tools: kiro",p.read_text())

if __name__=="__main__": unittest.main()
