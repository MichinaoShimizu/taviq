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


func TestInitDeinitRestoresHooksPath(t *testing.T) {
	dir:=t.TempDir()
	if err:=exec.Command("git","init",dir).Run();err!=nil{t.Fatal(err)}
	old,_:=os.Getwd();defer os.Chdir(old);os.Chdir(dir)
	if err:=exec.Command("git","config","core.hooksPath",".original").Run();err!=nil{t.Fatal(err)}
	if err:=initRepo();err!=nil{t.Fatal(err)}
	if err:=initRepo();err!=nil{t.Fatal(err)}
	if err:=deinitRepo();err!=nil{t.Fatal(err)}
	b,err:=exec.Command("git","config","--get","core.hooksPath").Output();if err!=nil{t.Fatal(err)}
	if strings.TrimSpace(string(b))!=".original"{t.Fatalf("hooksPath not restored: %s",b)}
}

func TestDoctorCoreDoesNotRequireGitHubActions(t *testing.T) {
	dir:=t.TempDir()
	if err:=exec.Command("git","init",dir).Run();err!=nil{t.Fatal(err)}
	old,_:=os.Getwd();defer os.Chdir(old);os.Chdir(dir)
	if err:=initRepo();err!=nil{t.Fatal(err)}
	x,err:=diagnose();if err!=nil{t.Fatal(err)}
	if !x["core_ready"].(bool){t.Fatal("expected core ready")}
	checks:=x["checks"].(map[string]bool)
	if checks["github_pr_summary"]{t.Fatal("GitHub Actions must remain optional")}
}
\n
func TestObserveAccumulatesOnSameHeadAndResetsOnNewHead(t *testing.T) {
	dir:=t.TempDir()
	if err:=exec.Command("git","init",dir).Run();err!=nil{t.Fatal(err)}
	old,_:=os.Getwd();defer os.Chdir(old);os.Chdir(dir)
	exec.Command("git","config","user.email","test@example.com").Run()
	exec.Command("git","config","user.name","Taviq Test").Run()
	os.WriteFile("a",[]byte("a"),0644);exec.Command("git","add","a").Run();exec.Command("git","commit","-m","a").Run()

	if err:=observe("claude","agent","sonnet");err!=nil{t.Fatal(err)}
	if err:=observe("codex","agent","gpt-x");err!=nil{t.Fatal(err)}
	if err:=observe("claude","agent","sonnet");err!=nil{t.Fatal(err)}
	b,_:=os.ReadFile(filepath.Join(dir,".taviq","runtime.json"))
	var x Runtime;if err:=json.Unmarshal(b,&x);err!=nil{t.Fatal(err)}
	if strings.Join(x.Tools,",")!="claude,codex"{t.Fatalf("tools=%v",x.Tools)}
	if strings.Join(x.Models,",")!="gpt-x,sonnet"{t.Fatalf("models=%v",x.Models)}
	oldHead:=x.BaseHead

	os.WriteFile("b",[]byte("b"),0644);exec.Command("git","add","b").Run();exec.Command("git","commit","-m","b").Run()
	if err:=observe("kiro","crew","");err!=nil{t.Fatal(err)}
	b,_=os.ReadFile(filepath.Join(dir,".taviq","runtime.json"));json.Unmarshal(b,&x)
	if x.BaseHead==oldHead{t.Fatal("expected new HEAD window")}
	if strings.Join(x.Tools,",")!="kiro"{t.Fatalf("expected reset tools, got %v",x.Tools)}
	if strings.Join(x.Modes,",")!="crew"{t.Fatalf("expected crew mode, got %v",x.Modes)}
}
