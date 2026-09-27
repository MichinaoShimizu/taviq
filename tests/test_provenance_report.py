import json, subprocess, sys, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).parents[1]
class IntegrationReportTests(unittest.TestCase):
    def test_report_from_explicit_inputs(self):
        with tempfile.TemporaryDirectory() as d:
            d=Path(d); changed=d/"changed.json"; sessions=d/"sessions.json"
            changed.write_text(json.dumps(["a.py","b.py"]))
            sessions.write_text(json.dumps([{"observed_files":["a.py"]}]))
            out=subprocess.check_output([sys.executable,str(ROOT/"scripts"/"provenance_report.py"),"--changed-files",str(changed),"--sessions",str(sessions)],text=True)
            r=json.loads(out)
            self.assertEqual(r["provenance"]["confirmed_files"],1)
            self.assertEqual(r["provenance"]["unknown_files"],1)
            self.assertIn("Unknown is not treated as human-only",r["check"]["details"][1])
if __name__=="__main__": unittest.main()
