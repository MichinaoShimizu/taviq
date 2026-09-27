import importlib.util, json, os, tempfile, unittest
from pathlib import Path
P=Path(__file__).parents[1]/"scripts"/"taviq_prepare_commit_msg.py"
S=importlib.util.spec_from_file_location("hook",P); M=importlib.util.module_from_spec(S); S.loader.exec_module(M)

class BasicHookTests(unittest.TestCase):
    def test_no_metadata_means_no_trailer(self):
        self.assertEqual(M.trailer_lines({},{}),[])
    def test_multi_value_trailer_is_stable(self):
        r={"tools":["codex","claude"],"modes":["agent"],"models":["z","a"]}
        lines=M.trailer_lines(r,{})
        self.assertEqual(lines[1],"Taviq-Tools: claude,codex")
        self.assertEqual(lines[2],"Taviq-Modes: agent")
        self.assertEqual(lines[3],"Taviq-Models: a,z")
    def test_environment_is_backward_compatible(self):
        lines=M.trailer_lines({},{"TAVIQ_TOOL":"kiro","TAVIQ_MODE":"agent"})
        self.assertIn("Taviq-Tools: kiro",lines)
    def test_metadata_budget(self):
        lines=M.trailer_lines({"tools":["claude","codex","kiro"],"modes":["agent","assist"],"models":["a","b"]},{})
        self.assertLess(len(("\n".join(lines)+"\n").encode()),1024)

if __name__=="__main__": unittest.main()