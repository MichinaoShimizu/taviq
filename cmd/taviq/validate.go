package main

import (
	"fmt"
	"os/exec"
	"sort"
	"strings"
)

// Commit validation checks that Taviq trailers follow the v1 schema. It checks
// format only: a well-formed trailer can still be hand-written, so a valid
// commit is Recorded, never verified.

// v1Fields are the trailer keys whose meaning v1 defines. Other Taviq-* keys
// are ignored so that optional fields added later stay readable.
var v1Fields = []string{"Taviq-Provenance", "Taviq-Tools", "Taviq-Modes", "Taviq-Models", "Taviq-Agents"}

var (
	knownTools = map[string]bool{"claude": true, "codex": true, "kiro": true}
	knownModes = map[string]bool{"assist": true, "generate": true, "agent": true, "crew": true, "mixed": true}
)

type CommitValidation struct {
	Commit string `json:"commit"`
	Status string `json:"status"` // recorded, unknown or invalid
	// Blocks counts provenance blocks when a squash left more than one.
	Blocks int      `json:"blocks,omitempty"`
	Errors []string `json:"errors,omitempty"`
}

// validateMessage checks every provenance block of a commit message. A
// squashed commit is recorded when each of its blocks is.
func validateMessage(message string) CommitValidation {
	blocks := provenanceBlocks(strings.Split(message, "\n"), "")
	if len(blocks) == 0 {
		return CommitValidation{Status: "unknown"}
	}
	r := CommitValidation{Status: "recorded"}
	if len(blocks) > 1 {
		r.Blocks = len(blocks)
	}
	for i, b := range blocks {
		status, errs := validateTrailers(b.Lines)
		if status == "invalid" {
			r.Status = "invalid"
		}
		for _, e := range errs {
			if len(blocks) > 1 {
				e = fmt.Sprintf("block %d: %s", i+1, e)
			}
			r.Errors = append(r.Errors, e)
		}
	}
	return r
}

// validateTrailers classifies one provenance block from its v1 field lines.
func validateTrailers(lines []string) (string, []string) {
	fields := map[string][]string{}
	for _, line := range lines {
		key, value, ok := strings.Cut(line, ":")
		if !ok {
			continue
		}
		for _, f := range v1Fields {
			if key == f {
				fields[f] = append(fields[f], strings.TrimSpace(value))
			}
		}
	}
	if len(fields) == 0 {
		return "unknown", nil
	}
	var errs []string
	for _, f := range v1Fields {
		if len(fields[f]) > 1 {
			errs = append(errs, fmt.Sprintf("%s appears %d times", f, len(fields[f])))
		}
	}
	first := func(f string) (string, bool) {
		if v := fields[f]; len(v) > 0 {
			return v[0], true
		}
		return "", false
	}
	switch v, ok := first("Taviq-Provenance"); {
	case !ok:
		errs = append(errs, "Taviq-Provenance is missing")
	case v != "v1":
		errs = append(errs, fmt.Sprintf("unsupported Taviq-Provenance: %q", v))
	}
	sets := map[string][]string{}
	for _, f := range v1Fields[1:] {
		raw, ok := first(f)
		if !ok {
			continue
		}
		values, err := parseTrailerSet(raw)
		if err != "" {
			errs = append(errs, f+": "+err)
		}
		sets[f] = values
	}
	if _, ok := first("Taviq-Tools"); !ok {
		errs = append(errs, "Taviq-Tools is missing")
	} else if len(sets["Taviq-Tools"]) == 0 {
		errs = append(errs, "Taviq-Tools is empty")
	}
	for _, f := range []string{"Taviq-Modes", "Taviq-Models", "Taviq-Agents"} {
		if _, ok := first(f); ok && len(sets[f]) == 0 {
			errs = append(errs, f+" is empty")
		}
	}
	for _, t := range sets["Taviq-Tools"] {
		if !knownTools[t] {
			errs = append(errs, fmt.Sprintf("Taviq-Tools: unsupported tool %q", t))
		}
	}
	for _, m := range sets["Taviq-Modes"] {
		if !knownModes[m] {
			errs = append(errs, fmt.Sprintf("Taviq-Modes: unsupported mode %q", m))
		}
	}
	tools, models := asSet(sets["Taviq-Tools"]), asSet(sets["Taviq-Models"])
	for _, a := range sets["Taviq-Agents"] {
		errs = append(errs, validateAgent(a, tools, models)...)
	}
	if len(errs) > 0 {
		return "invalid", errs
	}
	return "recorded", nil
}

// parseTrailerSet splits a comma-separated value and reports when it is not
// the deduplicated, lexically sorted form the hook writes.
func parseTrailerSet(raw string) ([]string, string) {
	if raw == "" {
		return nil, ""
	}
	parts := strings.Split(raw, ",")
	for _, p := range parts {
		if p == "" {
			return uniq(parts), "contains an empty value"
		}
		if strings.ContainsAny(p, " \t") {
			return uniq(parts), fmt.Sprintf("value %q contains whitespace", p)
		}
	}
	if canonical := uniq(parts); !sort.StringsAreSorted(parts) || len(canonical) != len(parts) {
		return canonical, "values must be deduplicated and sorted"
	}
	return parts, ""
}

func validateAgent(agent string, tools, models map[string]bool) []string {
	entry, model, hasModel := strings.Cut(agent, "=")
	tool, role, ok := strings.Cut(entry, ":")
	if !ok || tool == "" || role == "" || (hasModel && model == "") {
		return []string{fmt.Sprintf("Taviq-Agents: %q is not <tool>:<role>[=<model>]", agent)}
	}
	var errs []string
	if !agentRoles[role] {
		errs = append(errs, fmt.Sprintf("Taviq-Agents: unsupported role %q in %q", role, agent))
	}
	if !tools[tool] {
		errs = append(errs, fmt.Sprintf("Taviq-Agents: tool %q is not in Taviq-Tools", tool))
	}
	if hasModel && !models[model] {
		errs = append(errs, fmt.Sprintf("Taviq-Agents: model %q is not in Taviq-Models", model))
	}
	return errs
}

func asSet(xs []string) map[string]bool {
	out := map[string]bool{}
	for _, x := range xs {
		out[x] = true
	}
	return out
}

// validateCommits checks one commit, or every commit of a range such as
// origin/main..HEAD, newest first.
func validateCommits(rev string) ([]CommitValidation, error) {
	args := []string{"log", "--format=%x00%H%n%B"}
	if !strings.Contains(rev, "..") {
		args = append(args, "--no-walk")
	}
	out, err := exec.Command("git", append(args, rev, "--")...).Output()
	if err != nil {
		return nil, fmt.Errorf("cannot read commits for %s", rev)
	}
	results := []CommitValidation{}
	for _, record := range strings.Split(string(out), "\x00")[1:] {
		sha, message, _ := strings.Cut(record, "\n")
		r := validateMessage(message)
		r.Commit = sha
		results = append(results, r)
	}
	return results, nil
}

func validationReport(results []CommitValidation) map[string]any {
	summary := map[string]int{"commits": len(results), "recorded": 0, "unknown": 0, "invalid": 0}
	for _, r := range results {
		summary[r.Status]++
	}
	return map[string]any{"summary": summary, "commits": results}
}
