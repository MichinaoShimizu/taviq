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

    def test_explicit_file_path_is_allowed_but_content_is_not(self):
        safe=M.sanitize({"session_id":"s1","file_path":"src/app.py","content":"SECRET"})
        self.assertEqual(safe["file_path"],"src/app.py")
        self.assertNotIn("content",safe)

    def test_session_aggregates_explicit_files(self):
        with tempfile.TemporaryDirectory() as d:
            home=Path(d)
            base={"schema_version":1,"event":{"occurred_at":"2026-09-27T00:00:00+00:00"},"context":{"repository":"r","branch":"b","commit_sha":"abc"},"execution":{"session_id":"s1"}}
            e1={**base,"change":{"observed_file":"a.py"}}
            e2={**base,"change":{"observed_file":"b.py"}}
            M.update_session(e1,home); state=M.update_session(e2,home)
            self.assertEqual(state["observed_files"],["a.py","b.py"])
            self.assertEqual(state["commit_sha"],"abc")

    def test_coverage_is_provenance_not_ai_code_share(self):
        r=M.aggregate_coverage(["a.py","b.py","c.py"],[{"observed_files":["a.py","b.py"]}])
        self.assertEqual(r["confirmed_files"],2)
        self.assertEqual(r["unknown_files"],1)
        self.assertAlmostEqual(r["coverage"],66.6666666667)
        check=M.github_check_summary(r)
        self.assertIn("not percentage of code written by AI",check["details"][0])

    def test_unknown_is_not_human_only(self):
        r=M.aggregate_coverage(["a.py","b.py"],[{"observed_files":["a.py"]}])
        self.assertEqual(r["unknown_paths"],["b.py"])
        self.assertNotIn("human",r)

    def test_envelope_excludes_usage_and_identity(self):
        state={"session_id":"secret-session","repository":"r","branch":"b","commit_sha":"abc","observed_files":["src/a.py"],"usage":{"input_tokens":999},"user":"alice","cost":123}
        e=M.build_envelope(state)
        self.assertEqual(e["observed_files"],["src/a.py"])
        self.assertNotIn("usage",e); self.assertNotIn("cost",e); self.assertNotIn("user",e)
        self.assertNotEqual(e["session_ref"],"secret-session")

    def test_envelope_can_hash_paths(self):
        e=M.build_envelope({"session_id":"s","observed_files":["src/a.py"]},hash_paths=True)
        self.assertEqual(e["path_encoding"],"sha256")
        self.assertNotEqual(e["observed_files"][0],"src/a.py")

    def test_queue_envelope_writes_only_minimal_payload(self):
        with tempfile.TemporaryDirectory() as d:
            state={"session_id":"s1","repository":"r","observed_files":["a.py"],"usage":{"input_tokens":99},"cost":12}
            p=M.queue_envelope(state,Path(d))
            e=json.loads(p.read_text())
            self.assertEqual(e["kind"],"taviq-provenance-envelope")
            self.assertNotIn("usage",e); self.assertNotIn("cost",e)
            self.assertEqual(len(M.list_outbox(Path(d))),1)

    def test_event_store_is_jsonl(self):
        with tempfile.TemporaryDirectory() as d:
            event={"schema_version":1,"event":{"id":"x"}}
            path=M.append_event(event,Path(d))
            rows=path.read_text().splitlines()
            self.assertEqual(json.loads(rows[0]),event)

if __name__=="__main__": unittest.main()
