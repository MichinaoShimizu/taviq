package main

import (
	"regexp"
	"strings"
)

// Squashing moves each commit's trailers into the body of the new message:
// GitHub squash merges keep every commit's trailer paragraph and append their
// own Co-authored-by paragraph, and interactive rebase and `git merge --squash`
// concatenate the old messages. Git only reads the last paragraph as trailers,
// so Taviq also reads provenance blocks from the body.
//
// A provenance block is a paragraph in which every line has trailer form and at
// least one line is a v1 Taviq field. Prose that merely mentions a Taviq field
// never qualifies, because its other lines are not trailers.

type provenanceBlock struct {
	// Lines are the block's v1 Taviq field lines, trimmed.
	Lines []string
	// Index holds the message line number of each entry of Lines.
	Index []int
}

var trailerLine = regexp.MustCompile(`^[A-Za-z0-9][A-Za-z0-9-]*:( |$)`)

func isV1Field(line string) bool {
	key, _, ok := strings.Cut(line, ":")
	if !ok {
		return false
	}
	for _, f := range v1Fields {
		if key == f {
			return true
		}
	}
	return false
}

// provenanceBlocks finds provenance blocks in message lines. Lines starting
// with comment are paragraph separators; pass "" when the message has no
// comments. `git merge --squash` indents old messages, so lines are trimmed.
func provenanceBlocks(lines []string, comment string) []provenanceBlock {
	var blocks []provenanceBlock
	start := 0
	flush := func(end int) {
		para := lines[start:end]
		b := provenanceBlock{}
		for i, raw := range para {
			line := strings.TrimSpace(raw)
			if !trailerLine.MatchString(line) {
				return
			}
			if isV1Field(line) {
				b.Lines = append(b.Lines, line)
				b.Index = append(b.Index, start+i)
			}
		}
		if len(b.Lines) > 0 {
			blocks = append(blocks, b)
		}
	}
	for i, raw := range lines {
		if strings.TrimSpace(raw) == "" || (comment != "" && strings.HasPrefix(raw, comment)) {
			flush(i)
			start = i + 1
		}
	}
	flush(len(lines))
	return blocks
}

// mergeBlocks unions v1 blocks into one provenance. It reports false when a
// block does not declare v1, since sets of different versions cannot be merged.
func mergeBlocks(blocks []provenanceBlock) (Provenance, bool) {
	var p Provenance
	for _, b := range blocks {
		version := ""
		for _, line := range b.Lines {
			key, value, _ := strings.Cut(line, ":")
			values := strings.Split(strings.TrimSpace(value), ",")
			switch key {
			case "Taviq-Provenance":
				version = strings.TrimSpace(value)
			case "Taviq-Tools":
				p.Tools = append(p.Tools, values...)
			case "Taviq-Modes":
				p.Modes = append(p.Modes, values...)
			case "Taviq-Models":
				p.Models = append(p.Models, values...)
			case "Taviq-Agents":
				p.Agents = append(p.Agents, values...)
			}
		}
		if version != "v1" {
			return Provenance{}, false
		}
	}
	p.Tools, p.Modes, p.Models, p.Agents = uniq(trimAll(p.Tools)), uniq(trimAll(p.Modes)), uniq(trimAll(p.Models)), uniq(trimAll(p.Agents))
	return p, true
}

func trimAll(xs []string) []string {
	for i := range xs {
		xs[i] = strings.TrimSpace(xs[i])
	}
	return xs
}

func (p Provenance) trailers() []string {
	trailers := []string{"Taviq-Provenance: v1", "Taviq-Tools: " + strings.Join(p.Tools, ",")}
	if len(p.Modes) > 0 {
		trailers = append(trailers, "Taviq-Modes: "+strings.Join(p.Modes, ","))
	}
	if len(p.Models) > 0 {
		trailers = append(trailers, "Taviq-Models: "+strings.Join(p.Models, ","))
	}
	if len(p.Agents) > 0 {
		trailers = append(trailers, "Taviq-Agents: "+strings.Join(p.Agents, ","))
	}
	return trailers
}
