import importlib.util, tempfile, unittest
from pathlib import Path
P=Path(__file__).parents[1]/"src"/"taviq_relay.py"
S=importlib.util.spec_from_file_location("relay",P); M=importlib.util.module_from_spec(S); S.loader.exec_module(M)
class RelayTests(unittest.TestCase):
    def env(self):
        return {"schema_version":1,"kind":"taviq-provenance-envelope","session_ref":"abc","repository":"r","branch":"b","commit_sha":"c","tool":"claude","mode":"agent","model":None,"observed_files":["a.py"],"path_encoding":"plain"}
    def test_valid_envelope(self):
        self.assertEqual(M.validate_envelope(self.env()),(True,None))
    def test_rejects_raw_or_extra_fields(self):
        x=self.env(); x["prompt"]="secret"
        self.assertFalse(M.validate_envelope(x)[0])
        self.assertFalse(M.validate_envelope({"kind":"raw-event","session_ref":"x"})[0])
    def test_store_and_load_by_commit(self):
        with tempfile.TemporaryDirectory() as d:
            x=self.env(); M.store_envelope(Path(d),x)
            rows=M.load_commit(Path(d),"r","c")
            self.assertEqual(rows,[x])
if __name__=="__main__": unittest.main()
