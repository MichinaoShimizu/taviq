import importlib.util, json, tempfile, unittest
from pathlib import Path

ROOT=Path(__file__).parents[1]

def load(name,path):
    s=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

R=load("rt",ROOT/"scripts"/"set_runtime.py")
H=load("hook",ROOT/"scripts"/"taviq_prepare_commit_msg.py")
C=load("cp",ROOT/"scripts"/"commit_provenance.py")

class MultiProvenanceTests(unittest.TestCase):
    def test_runtime_accumulates_sets(self):
        with tempfile.TemporaryDirectory() as d:
            p=R.write("claude","agent","sonnet",d)
            R.write("codex","agent","gpt-x",d)
            R.write("claude","agent","sonnet",d)
            x=json.loads(p.read_text())
            self.assertEqual(x["tools"],["claude","codex"])
            self.assertEqual(x["modes"],["agent"])
            self.assertEqual(x["models"],["gpt-x","sonnet"])

    def test_commit_trailer_is_stable_multi_value(self):
        lines=H.trailer_lines({"tools":["claude","codex"],"modes":["agent"],"models":["gpt-x","sonnet"]})
        self.assertEqual(lines,[
            "Taviq-Provenance: v1",
            "Taviq-Tools: claude,codex",
            "Taviq-Modes: agent",
            "Taviq-Models: gpt-x,sonnet",
        ])

    def test_pr_counts_overlap_without_fake_percentage(self):
        rows=[
            {"status":"recorded","tools":["claude","codex"],"modes":["agent"],"models":[]},
            {"status":"recorded","tools":["claude"],"modes":["agent"],"models":[]},
            {"status":"unknown"},
        ]
        r=C.summarize(rows)
        self.assertEqual(r["coverage"],2/3*100)
        self.assertEqual(r["tools"],{"claude":2,"codex":1})
        self.assertEqual(r["multi_tool_commits"],1)
        self.assertNotIn("tool_percentage",r)

if __name__=="__main__": unittest.main()
