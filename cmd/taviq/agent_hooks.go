package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"regexp"
	"strings"
)

// agentHookIntegration describes an AI tool whose user-level hooks file uses
// the {"hooks": {"PreToolUse": [{"matcher", "hooks": [command...]}]}} shape.
// Claude Code settings and Codex hooks.json share it.
type agentHookIntegration struct {
	name    string // doctor key
	dir     func() (string, error)
	file    string
	matcher string
	// subcommand identifies Taviq-owned entries: only hook commands ending
	// with it are ever changed or removed.
	subcommand string
}

// PreToolUse on Bash runs before a `git commit` the agent makes itself, so
// that commit is observed even when an earlier commit in the same session
// already reset the observation.
var claudeCodeIntegration = agentHookIntegration{
	name:       "claude_code_hook",
	dir:        claudeConfigDir,
	file:       "settings.json",
	matcher:    "Edit|MultiEdit|Write|NotebookEdit|Bash",
	subcommand: " hook claude-code",
}

// Codex matchers are regular expressions over the tool name.
var codexIntegration = agentHookIntegration{
	name:       "codex_hook",
	dir:        codexHome,
	file:       "hooks.json",
	matcher:    "^(Bash|apply_patch|Edit|Write)$",
	subcommand: " hook codex",
}

var agentHookIntegrations = []agentHookIntegration{claudeCodeIntegration, codexIntegration}

// userDir returns the override from env, or ~/<name>.
func userDir(env, name string) (string, error) {
	if dir := os.Getenv(env); dir != "" {
		return dir, nil
	}
	home, err := os.UserHomeDir()
	if err != nil {
		return "", err
	}
	return filepath.Join(home, name), nil
}

// claudeConfigDir follows Claude Code's own CLAUDE_CONFIG_DIR override.
func claudeConfigDir() (string, error) { return userDir("CLAUDE_CONFIG_DIR", ".claude") }

// codexHome follows Codex's own CODEX_HOME override.
func codexHome() (string, error) { return userDir("CODEX_HOME", ".codex") }

func (i agentHookIntegration) path() (string, error) {
	dir, err := i.dir()
	if err != nil {
		return "", err
	}
	return filepath.Join(dir, i.file), nil
}

func loadHooksFile(path string) (map[string]any, error) {
	b, err := os.ReadFile(path)
	if os.IsNotExist(err) {
		return map[string]any{}, nil
	}
	if err != nil {
		return nil, err
	}
	settings := map[string]any{}
	if len(bytes.TrimSpace(b)) == 0 {
		return settings, nil
	}
	if err := json.Unmarshal(b, &settings); err != nil {
		return nil, fmt.Errorf("not valid JSON, left unchanged: %s: %w", path, err)
	}
	return settings, nil
}

// writeHooksFile replaces the file atomically and keeps its permissions.
// HTML escaping is off so user commands containing & < > are written as-is.
func writeHooksFile(path string, settings map[string]any) error {
	var buf bytes.Buffer
	enc := json.NewEncoder(&buf)
	enc.SetEscapeHTML(false)
	enc.SetIndent("", "  ")
	if err := enc.Encode(settings); err != nil {
		return err
	}
	mode := os.FileMode(0o644)
	if info, err := os.Stat(path); err == nil {
		mode = info.Mode().Perm()
	}
	tmp, err := os.CreateTemp(filepath.Dir(path), ".taviq-*")
	if err != nil {
		return err
	}
	defer os.Remove(tmp.Name())
	if _, err := tmp.Write(buf.Bytes()); err != nil {
		tmp.Close()
		return err
	}
	if err := tmp.Close(); err != nil {
		return err
	}
	if err := os.Chmod(tmp.Name(), mode); err != nil {
		return err
	}
	return os.Rename(tmp.Name(), path)
}

// withoutOwnHooks drops Taviq-owned hook commands and any matcher group left
// empty by that. Other groups are kept untouched.
func (i agentHookIntegration) withoutOwnHooks(groups []any) (kept []any, removed bool) {
	for _, g := range groups {
		m, ok := g.(map[string]any)
		hooks, isList := m["hooks"].([]any)
		if !ok || !isList {
			kept = append(kept, g)
			continue
		}
		var own []any
		for _, h := range hooks {
			hm, _ := h.(map[string]any)
			cmd, _ := hm["command"].(string)
			if strings.HasSuffix(cmd, i.subcommand) {
				removed = true
				continue
			}
			own = append(own, h)
		}
		if len(own) == 0 && len(hooks) > 0 {
			continue
		}
		if len(own) != len(hooks) {
			m["hooks"] = own
		}
		kept = append(kept, g)
	}
	return kept, removed
}

func preToolUseGroups(settings map[string]any) (map[string]any, []any, error) {
	hooks := map[string]any{}
	if v, ok := settings["hooks"]; ok {
		m, isMap := v.(map[string]any)
		if !isMap {
			return nil, nil, fmt.Errorf("\"hooks\" is not an object, left unchanged")
		}
		hooks = m
	}
	var groups []any
	if v, ok := hooks["PreToolUse"]; ok {
		list, isList := v.([]any)
		if !isList {
			return nil, nil, fmt.Errorf("\"hooks.PreToolUse\" is not a list, left unchanged")
		}
		groups = list
	}
	return hooks, groups, nil
}

// install wires the tool to `taviq hook <tool>`. It does nothing when the tool
// has no config directory on this machine.
func (i agentHookIntegration) install() error {
	dir, err := i.dir()
	if err != nil {
		return err
	}
	if !exists(dir) {
		return nil
	}
	path, err := i.path()
	if err != nil {
		return err
	}
	settings, err := loadHooksFile(path)
	if err != nil {
		return err
	}
	hooks, groups, err := preToolUseGroups(settings)
	if err != nil {
		return fmt.Errorf("%s: %w", path, err)
	}
	binary, err := taviqBinary()
	if err != nil {
		return err
	}
	groups, _ = i.withoutOwnHooks(groups)
	groups = append(groups, map[string]any{
		"matcher": i.matcher,
		"hooks": []any{map[string]any{
			"type":    "command",
			"command": shellQuote(binary) + i.subcommand,
		}},
	})
	hooks["PreToolUse"] = groups
	settings["hooks"] = hooks
	return writeHooksFile(path, settings)
}

// uninstall removes only Taviq-owned hook commands and leaves the file
// unwritten when there is nothing of Taviq's in it.
func (i agentHookIntegration) uninstall() error {
	path, err := i.path()
	if err != nil {
		return err
	}
	if !exists(path) {
		return nil
	}
	settings, err := loadHooksFile(path)
	if err != nil {
		return err
	}
	hooks, groups, err := preToolUseGroups(settings)
	if err != nil {
		return fmt.Errorf("%s: %w", path, err)
	}
	groups, removed := i.withoutOwnHooks(groups)
	if !removed {
		return nil
	}
	if len(groups) == 0 {
		delete(hooks, "PreToolUse")
	} else {
		hooks["PreToolUse"] = groups
	}
	if len(hooks) == 0 {
		delete(settings, "hooks")
	}
	return writeHooksFile(path, settings)
}

func (i agentHookIntegration) installed() bool {
	path, err := i.path()
	if err != nil {
		return false
	}
	settings, err := loadHooksFile(path)
	if err != nil {
		return false
	}
	_, groups, err := preToolUseGroups(settings)
	if err != nil {
		return false
	}
	_, found := i.withoutOwnHooks(groups)
	return found
}

func installAgentHooks() error {
	for _, i := range agentHookIntegrations {
		if err := i.install(); err != nil {
			return err
		}
	}
	return nil
}

func uninstallAgentHooks() error {
	for _, i := range agentHookIntegrations {
		if err := i.uninstall(); err != nil {
			return err
		}
	}
	return nil
}

// modelPattern keeps a tool-supplied model identifier from injecting commas,
// whitespace or extra trailer lines into the commit message.
var modelPattern = regexp.MustCompile(`^[A-Za-z0-9][A-Za-z0-9._:/@+-]{0,127}$`)

// agentHook handles a PreToolUse event from an AI tool. It never fails and
// never prints: output or a non-zero exit from a PreToolUse hook would affect
// the tool call the agent is about to make. Stdin is drained fully so the tool
// never sees a broken pipe. The model is recorded only when the tool itself
// supplies it in the event (trustModel); it is never guessed.
func agentHook(stdin io.Reader, tool string, trustModel bool) {
	b, _ := io.ReadAll(stdin)
	var event struct {
		Cwd   string `json:"cwd"`
		Model string `json:"model"`
	}
	_ = json.Unmarshal(b, &event)
	if event.Cwd != "" {
		if err := os.Chdir(event.Cwd); err != nil {
			return
		}
	}
	model := ""
	if trustModel && modelPattern.MatchString(event.Model) {
		model = event.Model
	}
	_ = observe(tool, "agent", model)
}
