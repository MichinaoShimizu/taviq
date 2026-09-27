import importlib.util, unittest
from pathlib import Path
P=Path(__file__).parents[1]/"scripts"/"commit_provenance.py"
S=importlib.util.spec_from_file_location("cp",P); M=importlib.util.module_from_spec(S); S.loader.exec_module(M)

class BasicE2ETests(unittest.TestCase):
    def test_overlapping_tool_counts_do_not_change_coverage(self):
        rows=[
            {"commit":"a","version":"v1","tools":["claude","codex"],"modes":["agent"],"models":[],"status":"recorded"},
            {"commit":"b","version":"v1","tools":["claude"],"modes":["agent"],"models":[],"status":"recorded"},
            {"commit":"c","status":"unknown"},
        ]
        r=M.summarize(rows)
        self.assertEqual(r["commits"],3)
        self.assertEqual(r["recorded"],2)
        self.assertEqual(r["unknown"],1)
        self.assertAlmostEqual(r["coverage"],66.6666666667)
        self.assertEqual(r["tools"],{"claude":2,"codex":1})
        self.assertEqual(r["multi_tool_commits"],1)

    def test_model_is_optional(self):
        r=M.summarize([{"commit":"a","version":"v1","tools":["kiro"],"modes":["agent"],"status":"recorded"}])
        self.assertEqual(r["models"],{})
        self.assertEqual(r["coverage"],100)

    def test_agent_roles_are_overlapping_counts(self):
        r=M.summarize([
            {"commit":"a","version":"v1","tools":["claude"],"agents":["claude:main=m1","claude:sub=m2"],"status":"recorded"},
            {"commit":"b","version":"v1","tools":["claude"],"agents":["claude:main=m1"],"status":"recorded"},
            {"commit":"c","version":"v1","tools":["kiro"],"status":"recorded"},
        ])
        self.assertEqual(r["agents"],{"claude:main=m1":2,"claude:sub=m2":1})

if __name__=="__main__": unittest.main()
