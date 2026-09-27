package main

import (
	"encoding/json"
	"os"
	"path/filepath"
	"reflect"
	"strings"
	"testing"
)

const userHooksFile = `{
  "model": "opus",
  "hooks": {
    "PreToolUse": [
      {"matcher": "Bash", "hooks": [{"type": "command", "command": "check && echo <ok>"}]},
      "unexpected"
    ],
    "Stop": [
      {"hooks": [{"type": "command", "command": "notify"}]}
    ]
  }
}
`

// agentSandbox points every tool config at temp dirs and returns the hooks
// file path of the integration under test.
func agentSandbox(t *testing.T, i agentHookIntegration, content string) string {
	t.Helper()
	t.Setenv("XDG_CONFIG_HOME", t.TempDir())
	t.Setenv("HOME", t.TempDir())
	t.Setenv("CLAUDE_CONFIG_DIR", t.TempDir())
	t.Setenv("CODEX_HOME", t.TempDir())
	path, err := i.path()
	if err != nil {
		t.Fatal(err)
	}
	if content != "" {
		if err := os.WriteFile(path, []byte(content), 0o600); err != nil {
			t.Fatal(err)
		}
	}
	return path
}

func readJSON(t *testing.T, path string) map[string]any {
	t.Helper()
	b, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	var x map[string]any
	if err := json.Unmarshal(b, &x); err != nil {
		t.Fatal(err)
	}
	return x
}

func forEachIntegration(t *testing.T, f func(t *testing.T, i agentHookIntegration)) {
	for _, i := range agentHookIntegrations {
		t.Run(i.name, func(t *testing.T) { f(t, i) })
	}
}

func TestAgentHookPreservesUserSettings(t *testing.T) {
	forEachIntegration(t, func(t *testing.T, i agentHookIntegration) {
		path := agentSandbox(t, i, userHooksFile)
		var original map[string]any
		_ = json.Unmarshal([]byte(userHooksFile), &original)

		for n := 0; n < 2; n++ {
			if err := i.install(); err != nil {
				t.Fatal(err)
			}
		}
		b, _ := os.ReadFile(path)
		if n := strings.Count(string(b), i.subcommand); n != 1 {
			t.Fatalf("want exactly one Taviq hook after repeated install, got %d:\n%s", n, b)
		}
		if !strings.Contains(string(b), "check && echo <ok>") {
			t.Fatalf("user command was escaped or lost:\n%s", b)
		}
		if !i.installed() {
			t.Fatal("doctor does not see the installed hook")
		}
		if info, _ := os.Stat(path); info.Mode().Perm() != 0o600 {
			t.Fatalf("file mode changed to %v", info.Mode().Perm())
		}

		if err := i.uninstall(); err != nil {
			t.Fatal(err)
		}
		if got := readJSON(t, path); !reflect.DeepEqual(got, original) {
			t.Fatalf("uninstall did not restore user settings:\n got %v\nwant %v", got, original)
		}
		if i.installed() {
			t.Fatal("hook still reported after uninstall")
		}
	})
}

func TestAgentHookIntegrationsDoNotTouchEachOther(t *testing.T) {
	agentSandbox(t, claudeCodeIntegration, "")
	if err := installAgentHooks(); err != nil {
		t.Fatal(err)
	}
	for _, i := range agentHookIntegrations {
		path, _ := i.path()
		b, _ := os.ReadFile(path)
		for _, other := range agentHookIntegrations {
			if other.name != i.name && strings.Contains(string(b), other.subcommand) {
				t.Fatalf("%s file contains the %s hook:\n%s", i.name, other.name, b)
			}
		}
	}
	if err := uninstallAgentHooks(); err != nil {
		t.Fatal(err)
	}
	for _, i := range agentHookIntegrations {
		path, _ := i.path()
		if got := readJSON(t, path); len(got) != 0 {
			t.Fatalf("%s: want empty file after uninstall, got %v", i.name, got)
		}
	}
}

func TestAgentHookSkipsMachineWithoutTool(t *testing.T) {
	forEachIntegration(t, func(t *testing.T, i agentHookIntegration) {
		agentSandbox(t, i, "")
		missing := filepath.Join(t.TempDir(), "absent")
		t.Setenv("CLAUDE_CONFIG_DIR", missing)
		t.Setenv("CODEX_HOME", missing)
		if err := i.install(); err != nil {
			t.Fatal(err)
		}
		if exists(missing) {
			t.Fatal("install created a tool config directory")
		}
	})
}

func TestAgentHookLeavesInvalidSettingsUntouched(t *testing.T) {
	forEachIntegration(t, func(t *testing.T, i agentHookIntegration) {
		for _, broken := range []string{"{ not json", `{"hooks": []}`, `{"hooks": {"PreToolUse": {}}}`} {
			path := agentSandbox(t, i, broken)
			if err := i.install(); err == nil {
				t.Fatalf("want visible failure on %q", broken)
			}
			if b, _ := os.ReadFile(path); string(b) != broken {
				t.Fatalf("invalid settings were rewritten: %q", b)
			}
		}
	})
}

// observedRuntime returns the trailer view of the recorded observations.
func observedRuntime(t *testing.T) Provenance {
	t.Helper()
	path, err := runtimePath()
	if err != nil {
		t.Fatal(err)
	}
	b, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	var x Runtime
	_ = json.Unmarshal(b, &x)
	return x.provenance()
}

func hookEventInRepo(t *testing.T, fields map[string]any) (string, string) {
	t.Helper()
	dir := enterRepo(t)
	if err := initMarker(); err != nil {
		t.Fatal(err)
	}
	if err := os.Chdir(t.TempDir()); err != nil {
		t.Fatal(err)
	}
	fields["cwd"] = dir
	event, _ := json.Marshal(fields)
	return dir, string(event)
}

// writeTranscript writes Claude Code transcript lines and returns the path.
func writeTranscript(t *testing.T, lines ...string) string {
	t.Helper()
	path := filepath.Join(t.TempDir(), "transcript.jsonl")
	if err := os.WriteFile(path, []byte(strings.Join(lines, "\n")+"\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	return path
}

func TestClaudeCodeHookObservesEventCwd(t *testing.T) {
	_, event := hookEventInRepo(t, map[string]any{"model": "claude-x", "tool_name": "Bash", "tool_input": map[string]any{"command": "git commit"}})
	agentHook(strings.NewReader(event), "claude", claudeCodeAgent)
	x := observedRuntime(t)
	if !reflect.DeepEqual(x.Tools, []string{"claude"}) || !reflect.DeepEqual(x.Modes, []string{"agent"}) || len(x.Models) != 0 || !reflect.DeepEqual(x.Agents, []string{"claude:main"}) {
		t.Fatalf("unexpected observation: %+v", x)
	}
}

func TestClaudeCodeHookRecordsTranscriptModel(t *testing.T) {
	transcript := writeTranscript(t,
		`{"type":"assistant","message":{"model":"claude-old"}}`,
		`{"type":"user","message":{"content":"hi"}}`,
		`{"type":"assistant","message":{"model":"claude-main"}}`,
		`{"type":"assistant","isSidechain":true,"message":{"model":"claude-subagent"}}`,
		`{"type":"assistant","message":{"model":"<synthetic>"}}`,
		`not json`,
	)
	_, event := hookEventInRepo(t, map[string]any{"transcript_path": transcript, "model": "claude-ignored"})
	agentHook(strings.NewReader(event), "claude", claudeCodeAgent)
	if x := observedRuntime(t); !reflect.DeepEqual(x.Models, []string{"claude-main"}) || !reflect.DeepEqual(x.Agents, []string{"claude:main=claude-main"}) {
		t.Fatalf("unexpected observation: %+v", x)
	}
}

// writeSubagentTranscript places a subagent transcript where Claude Code keeps
// it relative to the session transcript.
func writeSubagentTranscript(t *testing.T, session, agentID string, lines ...string) {
	t.Helper()
	dir := filepath.Join(strings.TrimSuffix(session, ".jsonl"), "subagents")
	if err := os.MkdirAll(dir, 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(dir, "agent-"+agentID+".jsonl"), []byte(strings.Join(lines, "\n")+"\n"), 0o644); err != nil {
		t.Fatal(err)
	}
}

func TestClaudeCodeHookRecordsSubagentModel(t *testing.T) {
	session := writeTranscript(t, `{"type":"assistant","message":{"model":"claude-main"}}`)
	writeSubagentTranscript(t, session, "a1b2",
		`{"type":"assistant","isSidechain":true,"agentId":"a1b2","message":{"model":"claude-sub"}}`,
		`{"type":"assistant","isSidechain":true,"agentId":"other","message":{"model":"claude-other"}}`,
	)
	_, event := hookEventInRepo(t, map[string]any{"transcript_path": session, "agent_id": "a1b2", "agent_type": "Explore"})
	agentHook(strings.NewReader(event), "claude", claudeCodeAgent)
	x := observedRuntime(t)
	if !reflect.DeepEqual(x.Models, []string{"claude-sub"}) || !reflect.DeepEqual(x.Agents, []string{"claude:sub=claude-sub"}) {
		t.Fatalf("unexpected observation: %+v", x)
	}
}

func TestClaudeCodeHookLeavesUnknownSubagentModelEmpty(t *testing.T) {
	session := writeTranscript(t, `{"type":"assistant","message":{"model":"claude-main"}}`)
	writeSubagentTranscript(t, session, "a1b2", `{"type":"assistant","message":{"model":"claude-planted"}}`)
	for _, agentID := range []string{"missing", "../a1b2", "a1b2/../../x"} {
		_, event := hookEventInRepo(t, map[string]any{"transcript_path": session, "agent_id": agentID})
		agentHook(strings.NewReader(event), "claude", claudeCodeAgent)
		if x := observedRuntime(t); len(x.Models) != 0 || !reflect.DeepEqual(x.Agents, []string{"claude:sub"}) {
			t.Fatalf("%s: unexpected observation: %+v", agentID, x)
		}
	}
	// Entries without the matching agentId are not the subagent's.
	_, event := hookEventInRepo(t, map[string]any{"transcript_path": session, "agent_id": "a1b2"})
	agentHook(strings.NewReader(event), "claude", claudeCodeAgent)
	if x := observedRuntime(t); len(x.Models) != 0 {
		t.Fatalf("model without matching agentId recorded: %+v", x)
	}
}

func TestClaudeCodeHookReadsOnlyTranscriptTail(t *testing.T) {
	filler := `{"type":"user","message":{"content":"` + strings.Repeat("x", transcriptTailBytes) + `"}}`
	transcript := writeTranscript(t, `{"type":"assistant","message":{"model":"claude-early"}}`, filler)
	_, event := hookEventInRepo(t, map[string]any{"transcript_path": transcript})
	agentHook(strings.NewReader(event), "claude", claudeCodeAgent)
	if x := observedRuntime(t); len(x.Models) != 0 {
		t.Fatalf("model read beyond the transcript tail: %+v", x)
	}
}

func TestClaudeCodeHookIgnoresUnusableTranscript(t *testing.T) {
	for _, transcript := range []string{"relative.jsonl", filepath.Join(t.TempDir(), "missing.jsonl"), t.TempDir()} {
		_, event := hookEventInRepo(t, map[string]any{"transcript_path": transcript})
		agentHook(strings.NewReader(event), "claude", claudeCodeAgent)
		if x := observedRuntime(t); !reflect.DeepEqual(x.Tools, []string{"claude"}) || len(x.Models) != 0 {
			t.Fatalf("%s: unexpected observation: %+v", transcript, x)
		}
	}
}

func TestAgentHookObservesEditedFileRepository(t *testing.T) {
	for _, field := range []string{"file_path", "notebook_path"} {
		repo, _ := hookEventInRepo(t, map[string]any{})
		elsewhere := t.TempDir()
		// The file and its directory may not exist yet (Write creates them).
		target := filepath.Join(repo, "new", "dir", "file.txt")
		event, _ := json.Marshal(map[string]any{"cwd": elsewhere, "tool_input": map[string]any{field: target}})
		agentHook(strings.NewReader(string(event)), "claude", claudeCodeAgent)
		if x := observedRuntime(t); !reflect.DeepEqual(x.Tools, []string{"claude"}) {
			t.Fatalf("%s: unexpected observation: %+v", field, x)
		}
		if entries, _ := os.ReadDir(elsewhere); len(entries) != 0 {
			t.Fatalf("%s: hook wrote to cwd: %v", field, entries)
		}
	}
}

func TestAgentHookResolvesRelativeFilePathAgainstCwd(t *testing.T) {
	repo, _ := hookEventInRepo(t, map[string]any{})
	event, _ := json.Marshal(map[string]any{"cwd": filepath.Dir(repo), "tool_input": map[string]any{"file_path": filepath.Join(filepath.Base(repo), "a.txt")}})
	agentHook(strings.NewReader(string(event)), "claude", claudeCodeAgent)
	if x := observedRuntime(t); !reflect.DeepEqual(x.Tools, []string{"claude"}) {
		t.Fatalf("unexpected observation: %+v", x)
	}
}

func TestCodexHookRecordsSuppliedModel(t *testing.T) {
	_, event := hookEventInRepo(t, map[string]any{"model": "gpt-5.3-codex", "tool_name": "Bash"})
	agentHook(strings.NewReader(event), "codex", codexAgent)
	x := observedRuntime(t)
	if !reflect.DeepEqual(x.Tools, []string{"codex"}) || !reflect.DeepEqual(x.Models, []string{"gpt-5.3-codex"}) {
		t.Fatalf("unexpected observation: %+v", x)
	}
}

func TestCodexHookRecordsAgentRole(t *testing.T) {
	_, event := hookEventInRepo(t, map[string]any{"model": "gpt-main"})
	agentHook(strings.NewReader(event), "codex", codexAgent)
	if x := observedRuntime(t); !reflect.DeepEqual(x.Agents, []string{"codex:main=gpt-main"}) {
		t.Fatalf("unexpected observation: %+v", x)
	}
	_, event = hookEventInRepo(t, map[string]any{"model": "gpt-sub", "agent_id": "019a-thread", "agent_type": "explorer"})
	agentHook(strings.NewReader(event), "codex", codexAgent)
	if x := observedRuntime(t); !reflect.DeepEqual(x.Models, []string{"gpt-sub"}) || !reflect.DeepEqual(x.Agents, []string{"codex:sub=gpt-sub"}) {
		t.Fatalf("unexpected observation: %+v", x)
	}
}

func TestCodexHookDropsUnsafeModel(t *testing.T) {
	_, event := hookEventInRepo(t, map[string]any{"model": "a,b\nTaviq-Tools: forged"})
	agentHook(strings.NewReader(event), "codex", codexAgent)
	if x := observedRuntime(t); len(x.Models) != 0 {
		t.Fatalf("unsafe model recorded: %+v", x)
	}
}

func TestAgentHookIgnoresNonRepository(t *testing.T) {
	outside := t.TempDir()
	old, _ := os.Getwd()
	t.Cleanup(func() { _ = os.Chdir(old) })
	if err := os.Chdir(outside); err != nil {
		t.Fatal(err)
	}
	agentHook(strings.NewReader(`{"cwd":"`+outside+`"}`), "codex", codexAgent)
	agentHook(strings.NewReader("not json"), "claude", claudeCodeAgent)
	if entries, _ := os.ReadDir(outside); len(entries) != 0 {
		t.Fatalf("hook wrote outside a repository: %v", entries)
	}
}
