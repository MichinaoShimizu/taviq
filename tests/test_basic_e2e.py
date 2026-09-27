import importlib.util, unittest
from pathlib import Path
P=Path(__file__).parents[1]/"scripts"/"commit_provenance.py"
S=importlib.util.spec_from_file_location("cp",P); M=importlib.util.module_from_spec(S); S.loader.exec_module(M)

class BasicE2ETests(unittest.TestCase):
    def test_mixed_confirmed_and_unknown_commits(self):
        rows=[
            {"commit":"a","version":"v1","tool":"claude","mode":"agent","status":"confirmed"},
            {"commit":"b","status":"unknown"},
            {"commit":"c","version":"v1","tool":"codex","mode":"agent","status":"confirmed"},
        ]
        r=M.summarize(rows)
        self.assertEqual(r["commits"],3)
        self.assertEqual(r["confirmed"],2)
        self.assertEqual(r["unknown"],1)
        self.assertAlmostEqual(r["coverage"],66.6666666667)
        self.assertEqual(r["tools"],["claude","codex"])

    def test_model_is_optional(self):
        r=M.summarize([{"commit":"a","version":"v1","tool":"kiro","mode":"agent","status":"confirmed"}])
        self.assertEqual(r["models"],[])
        self.assertEqual(r["coverage"],100)

if __name__=="__main__": unittest.main()
