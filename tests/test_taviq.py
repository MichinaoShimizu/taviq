import importlib.util, unittest
from pathlib import Path
P=Path(__file__).parents[1]/"taviq.py"
S=importlib.util.spec_from_file_location("taviq",P); M=importlib.util.module_from_spec(S); S.loader.exec_module(M)
class TestTaviq(unittest.TestCase):
    def test_metrics(self):
        x=[{"createdAt":"2026-09-01T00:00:00Z","mergedAt":"2026-09-02T00:00:00Z","additions":80,"deletions":20,"reviews":[{"submittedAt":"2026-09-01T06:00:00Z"}]}]
        r=M.summarize(x); self.assertEqual(r["cycle"],24); self.assertEqual(r["review"],6); self.assertEqual(r["size"],100)
    def test_roi(self):
        r=M.ai_roi({"seats":10,"license_cost":3000,"other_cost":20000,"net_hours_saved":40,"loaded_hourly_cost":5000})
        self.assertEqual(r["cost"],50000); self.assertEqual(r["value"],200000); self.assertEqual(r["roi"],300)
    def test_unrecorded_is_not_no_ai(self):
        x=[{"aiProvenance":"ai"},{"aiProvenance":"none"},{}]
        a,n,c,m=M.ai_compare(x); self.assertEqual(a["pr_count"],1); self.assertEqual(n["pr_count"],1); self.assertEqual(m,1); self.assertAlmostEqual(c,66.6666666667)
if __name__=="__main__": unittest.main()
