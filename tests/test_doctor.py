import importlib.util, subprocess, tempfile, unittest
from pathlib import Path
P=Path(__file__).parents[1]/"scripts"/"doctor.py"
S=importlib.util.spec_from_file_location("doctor",P); M=importlib.util.module_from_spec(S); S.loader.exec_module(M)

class DoctorTests(unittest.TestCase):
    def repo(self,d):
        r=Path(d)/"repo"; subprocess.check_call(["git","init",str(r)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); return r

    def test_incomplete_repo_is_not_ready(self):
        with tempfile.TemporaryDirectory() as d:
            r=self.repo(d)
            x=M.diagnose(r)
            self.assertFalse(x["core_ready"])
            self.assertEqual(x["status"],"incomplete")

    def test_core_can_be_ready_without_github_actions(self):
        with tempfile.TemporaryDirectory() as d:
            r=self.repo(d)
            (r/".taviq/hooks").mkdir(parents=True); (r/".taviq/hooks/prepare-commit-msg").write_text("")
            (r/"scripts").mkdir()
            (r/"scripts/set_runtime.py").write_text("")
            (r/"scripts/taviq_prepare_commit_msg.py").write_text("")
            subprocess.check_call(["git","-C",str(r),"config","core.hooksPath",".taviq/hooks"])
            x=M.diagnose(r)
            self.assertTrue(x["core_ready"])
            self.assertFalse(x["checks"]["github_pr_summary"])

if __name__=="__main__": unittest.main()
