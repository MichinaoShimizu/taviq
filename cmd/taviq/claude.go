package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"
)

// claudeHookSubcommand identifies Taviq-owned entries in Claude Code settings.
// Only hook commands ending with it are ever changed or removed.
const claudeHookSubcommand = " hook claude-code"

// claudeHookMatcher covers file edits and Bash. PreToolUse on Bash runs before
// a `git commit` Claude makes itself, so that commit is observed even when an
// earlier commit in the same session already reset the observation.
const claudeHookMatcher = "Edit|MultiEdit|Write|NotebookEdit|Bash"

// claudeConfigDir follows Claude Code's own CLAUDE_CONFIG_DIR override.
func claudeConfigDir() (string, error) {
	if dir := os.Getenv("CLAUDE_CONFIG_DIR"); dir != "" {
		return dir, nil
	}
	home, err := os.UserHomeDir()
	if err != nil {
		return "", err
	}
	return filepath.Join(home, ".claude"), nil
}

func claudeSettingsPath() (string, error) {
	dir, err := claudeConfigDir()
	if err != nil {
		return "", err
	}
	return filepath.Join(dir, "settings.json"), nil
}

func loadClaudeSettings(path string) (map[string]any, error) {
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
		return nil, fmt.Errorf("claude settings are not valid JSON, left unchanged: %s: %w", path, err)
	}
	return settings, nil
}

// writeClaudeSettings replaces the file atomically and keeps its permissions.
// HTML escaping is off so user commands containing & < > are written as-is.
func writeClaudeSettings(path string, settings map[string]any) error {
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
	tmp, err := os.CreateTemp(filepath.Dir(path), ".settings.json.taviq-*")
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

func isTaviqClaudeHook(h any) bool {
	m, ok := h.(map[string]any)
	if !ok {
		return false
	}
	cmd, _ := m["command"].(string)
	return strings.HasSuffix(cmd, claudeHookSubcommand)
}

// withoutTaviqClaudeHooks drops Taviq-owned hook commands from PreToolUse and
// any matcher group left empty by that. Other groups are kept untouched.
func withoutTaviqClaudeHooks(groups []any) (kept []any, removed bool) {
	for _, g := range groups {
		m, ok := g.(map[string]any)
		hooks, isList := m["hooks"].([]any)
		if !ok || !isList {
			kept = append(kept, g)
			continue
		}
		var own []any
		for _, h := range hooks {
			if isTaviqClaudeHook(h) {
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
			return nil, nil, fmt.Errorf("claude settings \"hooks\" is not an object, left unchanged")
		}
		hooks = m
	}
	var groups []any
	if v, ok := hooks["PreToolUse"]; ok {
		list, isList := v.([]any)
		if !isList {
			return nil, nil, fmt.Errorf("claude settings \"hooks.PreToolUse\" is not a list, left unchanged")
		}
		groups = list
	}
	return hooks, groups, nil
}

// installClaudeCodeIntegration wires Claude Code to `taviq hook claude-code`.
// It does nothing when Claude Code has no config directory on this machine.
func installClaudeCodeIntegration() error {
	dir, err := claudeConfigDir()
	if err != nil {
		return err
	}
	if !exists(dir) {
		return nil
	}
	path, err := claudeSettingsPath()
	if err != nil {
		return err
	}
	settings, err := loadClaudeSettings(path)
	if err != nil {
		return err
	}
	hooks, groups, err := preToolUseGroups(settings)
	if err != nil {
		return err
	}
	binary, err := taviqBinary()
	if err != nil {
		return err
	}
	groups, _ = withoutTaviqClaudeHooks(groups)
	groups = append(groups, map[string]any{
		"matcher": claudeHookMatcher,
		"hooks": []any{map[string]any{
			"type":    "command",
			"command": shellQuote(binary) + claudeHookSubcommand,
		}},
	})
	hooks["PreToolUse"] = groups
	settings["hooks"] = hooks
	return writeClaudeSettings(path, settings)
}

// uninstallClaudeCodeIntegration removes only Taviq-owned hook commands and
// leaves the file unwritten when there is nothing of Taviq's in it.
func uninstallClaudeCodeIntegration() error {
	path, err := claudeSettingsPath()
	if err != nil {
		return err
	}
	if !exists(path) {
		return nil
	}
	settings, err := loadClaudeSettings(path)
	if err != nil {
		return err
	}
	hooks, groups, err := preToolUseGroups(settings)
	if err != nil {
		return err
	}
	groups, removed := withoutTaviqClaudeHooks(groups)
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
	return writeClaudeSettings(path, settings)
}

func claudeCodeIntegrationInstalled() bool {
	path, err := claudeSettingsPath()
	if err != nil {
		return false
	}
	settings, err := loadClaudeSettings(path)
	if err != nil {
		return false
	}
	_, groups, err := preToolUseGroups(settings)
	if err != nil {
		return false
	}
	_, found := withoutTaviqClaudeHooks(groups)
	return found
}

// claudeCodeHook handles a Claude Code hook event. It never fails and never
// prints: a non-zero exit or output from a PreToolUse hook would affect the
// tool call Claude is about to make. Stdin is drained fully so Claude never
// sees a broken pipe.
func claudeCodeHook(stdin io.Reader) {
	b, _ := io.ReadAll(stdin)
	var event struct {
		Cwd string `json:"cwd"`
	}
	_ = json.Unmarshal(b, &event)
	if event.Cwd != "" {
		if err := os.Chdir(event.Cwd); err != nil {
			return
		}
	}
	_ = observe("claude", "agent", "")
}
