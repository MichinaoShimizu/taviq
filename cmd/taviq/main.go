package main

import (
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"sort"
	"strings"
)

type Runtime struct {
	SchemaVersion int      `json:"schema_version"`
	BaseHead      string   `json:"base_head,omitempty"`
	Tools         []string `json:"tools"`
	Modes         []string `json:"modes"`
	Models        []string `json:"models"`
}

const hookScript = `#!/bin/sh
exec taviq hook prepare-commit-msg "$1"
`

type MachineState struct {
	SchemaVersion int `json:"schema_version"`
	Installed     bool `json:"installed"`
}

func machineConfigDir() (string, error) {
	base, err := os.UserConfigDir()
	if err != nil {
		return "", err
	}
	return filepath.Join(base, "taviq"), nil
}

func machineInstall() error {
	dir, err := machineConfigDir()
	if err != nil {
		return err
	}
	if err := os.MkdirAll(dir, 0o755); err != nil {
		return err
	}
	state := MachineState{SchemaVersion: 1, Installed: true}
	b, err := json.MarshalIndent(state, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(filepath.Join(dir, "state.json"), b, 0o644)
}

func machineUninstall() error {
	dir, err := machineConfigDir()
	if err != nil {
		return err
	}
	_ = os.Remove(filepath.Join(dir, "state.json"))
	return os.Remove(dir)
}

func root() (string, error) {
	b, err := exec.Command("git", "rev-parse", "--show-toplevel").Output()
	if err != nil {
		return "", err
	}
	return strings.TrimSpace(string(b)), nil
}

func gitHead() string {
	b, err := exec.Command("git", "rev-parse", "HEAD").Output()
	if err != nil {
		return ""
	}
	return strings.TrimSpace(string(b))
}

func uniq(xs []string) []string {
	seen := map[string]bool{}
	out := []string{}
	for _, x := range xs {
		if x != "" && !seen[x] {
			seen[x] = true
			out = append(out, x)
		}
	}
	sort.Strings(out)
	return out
}

func observe(tool, mode, model string) error {
	if tool != "claude" && tool != "codex" && tool != "kiro" {
		return fmt.Errorf("unsupported tool: %s", tool)
	}
	r, err := root()
	if err != nil {
		return err
	}
	dir := filepath.Join(r, ".taviq")
	if err := os.MkdirAll(dir, 0755); err != nil {
		return err
	}
	path := filepath.Join(dir, "runtime.json")
	current := gitHead()
	var x Runtime
	if b, err := os.ReadFile(path); err == nil {
		_ = json.Unmarshal(b, &x)
	}
	if x.BaseHead != current {
		x = Runtime{SchemaVersion: 1, BaseHead: current, Tools: []string{}, Modes: []string{}, Models: []string{}}
	}
	x.SchemaVersion = 1
	x.BaseHead = current
	x.Tools = uniq(append(x.Tools, tool))
	if mode != "" {
		x.Modes = uniq(append(x.Modes, mode))
	}
	if model != "" {
		x.Models = uniq(append(x.Models, model))
	}
	b, err := json.Marshal(x)
	if err != nil {
		return err
	}
	return os.WriteFile(path, b, 0644)
}

func hook(message string) error {
	r, err := root()
	if err != nil {
		return err
	}
	var x Runtime
	if data, err := os.ReadFile(filepath.Join(r, ".taviq", "runtime.json")); err == nil {
		_ = json.Unmarshal(data, &x)
	}
	if tool := os.Getenv("TAVIQ_TOOL"); tool != "" {
		x.Tools = append(x.Tools, tool)
	}
	if mode := os.Getenv("TAVIQ_MODE"); mode != "" {
		x.Modes = append(x.Modes, mode)
	}
	if model := os.Getenv("TAVIQ_MODEL"); model != "" {
		x.Models = append(x.Models, model)
	}
	x.Tools = uniq(x.Tools)
	x.Modes = uniq(x.Modes)
	x.Models = uniq(x.Models)
	if len(x.Tools) == 0 {
		return nil
	}
	body, err := os.ReadFile(message)
	if err != nil {
		return err
	}
	if strings.Contains(string(body), "Taviq-Provenance:") {
		return nil
	}
	lines := []string{"Taviq-Provenance: v1", "Taviq-Tools: " + strings.Join(x.Tools, ",")}
	if len(x.Modes) > 0 {
		lines = append(lines, "Taviq-Modes: "+strings.Join(x.Modes, ","))
	}
	if len(x.Models) > 0 {
		lines = append(lines, "Taviq-Models: "+strings.Join(x.Models, ","))
	}
	text := strings.TrimRight(string(body), "\n") + "\n\n" + strings.Join(lines, "\n") + "\n"
	return os.WriteFile(message, []byte(text), 0644)
}

func initRepo() error {
	r, err := root()
	if err != nil {
		return err
	}
	dir := filepath.Join(r, ".taviq", "hooks")
	if err := os.MkdirAll(dir, 0755); err != nil {
		return err
	}
	state := filepath.Join(r, ".taviq", "install-state")
	if _, err := os.Stat(state); os.IsNotExist(err) {
		out, _ := exec.Command("git", "config", "--get", "core.hooksPath").Output()
		if err := os.WriteFile(state, []byte(strings.TrimSpace(string(out))), 0644); err != nil {
			return err
		}
	}
	target := filepath.Join(dir, "prepare-commit-msg")
	if err := os.WriteFile(target, []byte(hookScript), 0755); err != nil {
		return err
	}
	return exec.Command("git", "config", "core.hooksPath", ".taviq/hooks").Run()
}

func deinitRepo() error {
	r, err := root()
	if err != nil {
		return err
	}
	state := filepath.Join(r, ".taviq", "install-state")
	previous := ""
	if b, err := os.ReadFile(state); err == nil {
		previous = string(b)
	}
	if previous != "" {
		_ = exec.Command("git", "config", "core.hooksPath", previous).Run()
	} else {
		_ = exec.Command("git", "config", "--unset", "core.hooksPath").Run()
	}
	for _, p := range []string{
		filepath.Join(r, ".taviq", "hooks", "prepare-commit-msg"),
		filepath.Join(r, ".taviq", "runtime.json"),
		state,
	} {
		_ = os.Remove(p)
	}
	return nil
}

func exists(path string) bool {
	_, err := os.Stat(path)
	return err == nil
}

func diagnose() (map[string]any, error) {
	r, err := root()
	if err != nil {
		return nil, err
	}
	hooksOut, _ := exec.Command("git", "config", "--get", "core.hooksPath").Output()
	checks := map[string]bool{
		"git_repository":          true,
		"hooks_path":              strings.TrimSpace(string(hooksOut)) == ".taviq/hooks",
		"prepare_commit_msg_hook": exists(filepath.Join(r, ".taviq", "hooks", "prepare-commit-msg")),
		"github_pr_summary":       exists(filepath.Join(r, ".github", "workflows", "taviq-basic.yml")),
	}
	core := checks["hooks_path"] && checks["prepare_commit_msg_hook"]
	status := "incomplete"
	if core {
		status = "ready"
	}
	return map[string]any{"status": status, "core_ready": core, "checks": checks}, nil
}

func fail(err error) {
	fmt.Fprintln(os.Stderr, err)
	os.Exit(1)
}

func main() {
	if len(os.Args) < 2 {
		fmt.Println("usage: taviq <install|uninstall|init|deinit|doctor|observe|hook>")
		return
	}

	switch os.Args[1] {
	case "install":
		if err := machineInstall(); err != nil {
			fail(err)
		}
	case "uninstall":
		if err := machineUninstall(); err != nil && !os.IsNotExist(err) {
			fail(err)
		}
	case "init":
		if err := initRepo(); err != nil {
			fail(err)
		}
	case "deinit":
		if err := deinitRepo(); err != nil {
			fail(err)
		}
	case "doctor":
		x, err := diagnose()
		if err != nil {
			fail(err)
		}
		b, _ := json.MarshalIndent(x, "", "  ")
		fmt.Println(string(b))
		if !x["core_ready"].(bool) {
			os.Exit(1)
		}
	case "observe":
		if len(os.Args) < 4 {
			fail(fmt.Errorf("usage: taviq observe <tool> <mode> [model]"))
		}
		model := ""
		if len(os.Args) >= 5 {
			model = os.Args[4]
		}
		if err := observe(os.Args[2], os.Args[3], model); err != nil {
			fail(err)
		}
	case "hook":
		if len(os.Args) != 4 || os.Args[2] != "prepare-commit-msg" {
			fail(fmt.Errorf("usage: taviq hook prepare-commit-msg <message-file>"))
		}
		if err := hook(os.Args[3]); err != nil {
			fail(err)
		}
	default:
		fail(fmt.Errorf("unknown command: %s", os.Args[1]))
	}
}
