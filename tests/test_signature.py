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
    def test_commit_verification_states_are_separate(self):
        import importlib.util
        cp_path=Path(__file__).parents[1]/"scripts"/"commit_provenance.py"
        sp=importlib.util.spec_from_file_location("cp",cp_path); cp=importlib.util.module_from_spec(sp); sp.loader.exec_module(cp)
        x=self.payload(); sig=M.sign(x,"secret")
        row={"version":"v1","tool":"claude","mode":"agent","model":"","ref":"abc","signature":"hmac-sha256:"+sig}
        self.assertEqual(cp.verify_row(row,"owner/repo","secret"),"verified")
        row["tool"]="codex"
        self.assertEqual(cp.verify_row(row,"owner/repo","secret"),"invalid")
        self.assertEqual(cp.verify_row({"version":"v1","tool":"claude"},"owner/repo","secret"),"unverified")
        self.assertEqual(cp.verify_row({},"owner/repo","secret"),"unknown")

if __name__=="__main__": unittest.main()
