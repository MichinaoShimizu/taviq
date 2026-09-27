package main

import (
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"
)

func TestHookGoldenTrailer(t *testing.T) {
	dir:=t.TempDir()
	if err:=exec.Command("git","init",dir).Run();err!=nil{t.Fatal(err)}
	old,_:=os.Getwd(); defer os.Chdir(old); os.Chdir(dir)
	msg:=filepath.Join(dir,"msg")
	os.WriteFile(msg,[]byte("Change\n"),0644)
	os.Setenv("TAVIQ_TOOL","claude"); defer os.Unsetenv("TAVIQ_TOOL")
	os.Setenv("TAVIQ_MODE","agent"); defer os.Unsetenv("TAVIQ_MODE")
	if err:=hook(msg);err!=nil{t.Fatal(err)}
	b,_:=os.ReadFile(msg); got:=string(b)
	want:="Change\n\nTaviq-Provenance: v1\nTaviq-Tools: claude\nTaviq-Modes: agent\n"
	if got!=want{t.Fatalf("golden mismatch\nwant=%q\ngot =%q",want,got)}
}

func TestHookMultiValueSorted(t *testing.T) {
	dir:=t.TempDir()
	if err:=exec.Command("git","init",dir).Run();err!=nil{t.Fatal(err)}
	old,_:=os.Getwd(); defer os.Chdir(old); os.Chdir(dir)
	os.Mkdir(filepath.Join(dir,".taviq"),0755)
	os.WriteFile(filepath.Join(dir,".taviq","runtime.json"),[]byte(`{"tools":["codex","claude"],"modes":["agent"],"models":["z","a"]}`),0644)
	msg:=filepath.Join(dir,"msg"); os.WriteFile(msg,[]byte("X\n"),0644)
	if err:=hook(msg);err!=nil{t.Fatal(err)}
	b,_:=os.ReadFile(msg); s:=string(b)
	for _,want:=range []string{"Taviq-Tools: claude,codex","Taviq-Modes: agent","Taviq-Models: a,z"} {
		if !strings.Contains(s,want){t.Fatalf("missing %s in %s",want,s)}
	}
}
