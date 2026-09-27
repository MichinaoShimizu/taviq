import importlib.util, unittest
from pathlib import Path
P=Path(__file__).parents[1]/"scripts"/"sign_provenance.py"
S=importlib.util.spec_from_file_location("sig",P); M=importlib.util.module_from_spec(S); S.loader.exec_module(M)
class SignatureTests(unittest.TestCase):
    def payload(self):
        return {"version":"v1","tool":"claude","mode":"agent","model":"","repository":"owner/repo","ref":"abc"}
    def test_round_trip(self):
        x=self.payload(); sig=M.sign(x,"secret")
        self.assertTrue(M.verify(x,"secret",sig))
    def test_modified_tool_fails(self):
        x=self.payload(); sig=M.sign(x,"secret"); x["tool"]="codex"
        self.assertFalse(M.verify(x,"secret",sig))
    def test_wrong_repo_fails(self):
        x=self.payload(); sig=M.sign(x,"secret"); x["repository"]="other/repo"
        self.assertFalse(M.verify(x,"secret",sig))
if __name__=="__main__": unittest.main()
