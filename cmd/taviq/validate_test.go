package main

import (
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"
)

func TestValidateTrailers(t *testing.T) {
	cases := []struct {
		name   string
		lines  []string
		status string
		err    string
	}{
		{"no trailers", nil, "unknown", ""},
		{"other trailers only", []string{"Co-Authored-By: someone"}, "unknown", ""},
		{"minimal", []string{"Taviq-Provenance: v1", "Taviq-Tools: claude"}, "recorded", ""},
		{"full", []string{
			"Taviq-Provenance: v1",
			"Taviq-Tools: claude,codex",
			"Taviq-Modes: agent",
			"Taviq-Models: gpt-model,model-main",
			"Taviq-Agents: claude:main=model-main,claude:sub,codex:main=gpt-model",
		}, "recorded", ""},
		{"future optional field ignored", []string{"Taviq-Provenance: v1", "Taviq-Tools: kiro", "Taviq-Future: x"}, "recorded", ""},
		{"missing provenance", []string{"Taviq-Tools: claude"}, "invalid", "Taviq-Provenance is missing"},
		{"unsupported version", []string{"Taviq-Provenance: v2", "Taviq-Tools: claude"}, "invalid", "unsupported Taviq-Provenance"},
		{"missing tools", []string{"Taviq-Provenance: v1"}, "invalid", "Taviq-Tools is missing"},
		{"empty tools", []string{"Taviq-Provenance: v1", "Taviq-Tools:"}, "invalid", "Taviq-Tools is empty"},
		{"duplicate field", []string{"Taviq-Provenance: v1", "Taviq-Tools: claude", "Taviq-Tools: codex"}, "invalid", "appears 2 times"},
		{"unsorted", []string{"Taviq-Provenance: v1", "Taviq-Tools: codex,claude"}, "invalid", "deduplicated and sorted"},
		{"duplicated value", []string{"Taviq-Provenance: v1", "Taviq-Tools: claude,claude"}, "invalid", "deduplicated and sorted"},
		{"empty value", []string{"Taviq-Provenance: v1", "Taviq-Tools: claude,"}, "invalid", "empty value"},
		{"whitespace", []string{"Taviq-Provenance: v1", "Taviq-Tools: claude, codex"}, "invalid", "whitespace"},
		{"unknown tool", []string{"Taviq-Provenance: v1", "Taviq-Tools: other"}, "invalid", "unsupported tool"},
		{"unknown mode", []string{"Taviq-Provenance: v1", "Taviq-Tools: claude", "Taviq-Modes: autopilot"}, "invalid", "unsupported mode"},
		{"malformed agent", []string{"Taviq-Provenance: v1", "Taviq-Tools: claude", "Taviq-Agents: claude"}, "invalid", "is not <tool>:<role>"},
		{"unknown role", []string{"Taviq-Provenance: v1", "Taviq-Tools: claude", "Taviq-Agents: claude:lead"}, "invalid", "unsupported role"},
		{"agent tool not in tools", []string{"Taviq-Provenance: v1", "Taviq-Tools: claude", "Taviq-Agents: codex:main"}, "invalid", "not in Taviq-Tools"},
		{"agent model not in models", []string{"Taviq-Provenance: v1", "Taviq-Tools: claude", "Taviq-Agents: claude:main=model-a"}, "invalid", "not in Taviq-Models"},
	}
	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			status, errs := validateTrailers(c.lines)
			if status != c.status {
				t.Fatalf("status = %s, want %s (errors %v)", status, c.status, errs)
			}
			if c.err != "" && !strings.Contains(strings.Join(errs, "\n"), c.err) {
				t.Fatalf("errors %v do not mention %q", errs, c.err)
			}
		})
	}
}

// The hook's own output must always pass validation.
func TestValidateAcceptsHookOutput(t *testing.T) {
	dir := enterRepo(t)
	configureGit()
	if err := initMarker(); err != nil {
		t.Fatal(err)
	}
	_ = exec.Command("git", "commit", "--allow-empty", "-m", "base").Run()
	if err := observeAgent("codex", "agent", "gpt-model", "main"); err != nil {
		t.Fatal(err)
	}
	if err := observeAgent("claude", "agent", "model-main", "main"); err != nil {
		t.Fatal(err)
	}
	if err := observeAgent("claude", "agent", "", "sub"); err != nil {
		t.Fatal(err)
	}
	msg := filepath.Join(dir, "msg")
	_ = os.WriteFile(msg, []byte("Change\n"), 0o644)
	if err := hook(msg); err != nil {
		t.Fatal(err)
	}
	if out, err := exec.Command("git", "commit", "--allow-empty", "-F", msg).CombinedOutput(); err != nil {
		t.Fatal(string(out))
	}
	results, err := validateCommits("HEAD~1..HEAD")
	if err != nil {
		t.Fatal(err)
	}
	if len(results) != 1 || results[0].Status != "recorded" {
		t.Fatalf("got %+v", results)
	}
}

func TestValidateCommitsRange(t *testing.T) {
	enterRepo(t)
	configureGit()
	commit := func(msg string) {
		if out, err := exec.Command("git", "commit", "--allow-empty", "-m", msg).CombinedOutput(); err != nil {
			t.Fatal(string(out))
		}
	}
	commit("base")
	commit("human or unobserved")
	commit("ai\n\nTaviq-Provenance: v1\nTaviq-Tools: claude")
	commit("broken\n\nTaviq-Provenance: v1\nTaviq-Tools: codex,claude")

	results, err := validateCommits("HEAD~3..HEAD")
	if err != nil {
		t.Fatal(err)
	}
	var got []string
	for _, r := range results {
		got = append(got, r.Status)
	}
	if strings.Join(got, ",") != "invalid,recorded,unknown" {
		t.Fatalf("statuses = %v", got)
	}
	summary := validationReport(results)["summary"].(map[string]int)
	if summary["commits"] != 3 || summary["invalid"] != 1 || summary["recorded"] != 1 || summary["unknown"] != 1 {
		t.Fatalf("summary = %v", summary)
	}

	single, err := validateCommits("HEAD")
	if err != nil {
		t.Fatal(err)
	}
	if len(single) != 1 || single[0].Status != "invalid" {
		t.Fatalf("single = %+v", single)
	}

	if _, err := validateCommits("no-such-rev"); err == nil {
		t.Fatal("expected error for unknown revision")
	}
}

// githubSquash mirrors the message GitHub writes for a squash merge: each
// commit's trailer paragraph stays in the body and GitHub appends its own
// Co-authored-by paragraph, which Git then reads as the only trailer block.
const githubSquash = `Add feature (#12)

* First change

Explain the change. The trailer looks like
Taviq-Tools: kiro
in prose, which is not provenance.

Co-Authored-By: Someone <someone@example.com>
Taviq-Provenance: v1
Taviq-Tools: claude
Taviq-Modes: agent
Taviq-Models: model-a
Taviq-Agents: claude:main=model-a

* Second change

Taviq-Provenance: v1
Taviq-Tools: codex
Taviq-Modes: agent

---------

Co-authored-by: Someone <someone@example.com>
`

func TestValidateMessageSquash(t *testing.T) {
	r := validateMessage(githubSquash)
	if r.Status != "recorded" || r.Blocks != 2 || len(r.Errors) != 0 {
		t.Fatalf("got %+v", r)
	}
	broken := strings.Replace(githubSquash, "Taviq-Tools: codex", "Taviq-Tools: codex,claude", 1)
	r = validateMessage(broken)
	if r.Status != "invalid" || !strings.Contains(strings.Join(r.Errors, "\n"), "block 2:") {
		t.Fatalf("got %+v", r)
	}
	if r := validateMessage("Prose\n\nmentions Taviq-Provenance: v1 inline\n"); r.Status != "unknown" {
		t.Fatalf("prose counted as provenance: %+v", r)
	}
}

func TestValidateCommitsSquashMerge(t *testing.T) {
	dir := enterRepo(t)
	configureGit()
	msg := filepath.Join(dir, "msg")
	_ = os.WriteFile(msg, []byte(githubSquash), 0o644)
	if out, err := exec.Command("git", "commit", "--allow-empty", "--cleanup=verbatim", "-F", msg).CombinedOutput(); err != nil {
		t.Fatal(string(out))
	}
	results, err := validateCommits("HEAD")
	if err != nil {
		t.Fatal(err)
	}
	if len(results) != 1 || results[0].Status != "recorded" || results[0].Blocks != 2 {
		t.Fatalf("got %+v", results)
	}
}
