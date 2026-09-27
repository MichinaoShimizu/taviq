import importlib.util, json, tempfile, unittest
from pathlib import Path

P=Path(__file__).parents[1]/"src"/"taviq_provenance.py"
S=importlib.util.spec_from_file_location("prov",P); M=importlib.util.module_from_spec(S); S.loader.exec_module(M)

class ProvenanceTests(unittest.TestCase):
    def test_sensitive_content_is_dropped(self):
        raw={"session_id":"s1","hook_event_name":"Stop","model":"claude-test","prompt":"SECRET","response":"SECRET2","tool_input":{"code":"SECRET3"},"usage":{"input_tokens":10,"output_tokens":4}}
        safe=M.sanitize(raw)
        self.assertNotIn("prompt",safe); self.assertNotIn("response",safe); self.assertNotIn("tool_input",safe)
        self.assertEqual(safe["usage"]["input_tokens"],10)

    def test_unknown_fields_are_not_persisted(self):
        safe=M.sanitize({"session_id":"s1","mystery":{"private":"x"},"cwd":"/tmp"})
        self.assertEqual(set(safe),{"session_id","cwd"})

    def test_event_store_is_jsonl(self):
        with tempfile.TemporaryDirectory() as d:
            event={"schema_version":1,"event":{"id":"x"}}
            path=M.append_event(event,Path(d))
            rows=path.read_text().splitlines()
            self.assertEqual(json.loads(rows[0]),event)

if __name__=="__main__": unittest.main()
