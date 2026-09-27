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

func root() (string,error) {
	b,err:=exec.Command("git","rev-parse","--show-toplevel").Output()
	if err!=nil{return "",err}
	return strings.TrimSpace(string(b)),nil
}

func hook(message string) error {
	r,err:=root(); if err!=nil{return err}
	data,err:=os.ReadFile(filepath.Join(r,".taviq","runtime.json"))
	var x Runtime
	if err==nil {_=json.Unmarshal(data,&x)}
	if t:=os.Getenv("TAVIQ_TOOL"); t!="" {x.Tools=append(x.Tools,t)}
	if m:=os.Getenv("TAVIQ_MODE"); m!="" {x.Modes=append(x.Modes,m)}
	if m:=os.Getenv("TAVIQ_MODEL"); m!="" {x.Models=append(x.Models,m)}
	x.Tools=uniq(x.Tools); x.Modes=uniq(x.Modes); x.Models=uniq(x.Models)
	if len(x.Tools)==0{return nil}
	body,err:=os.ReadFile(message); if err!=nil{return err}
	if strings.Contains(string(body),"Taviq-Provenance:"){return nil}
	lines:=[]string{"Taviq-Provenance: v1","Taviq-Tools: "+strings.Join(x.Tools,",")}
	if len(x.Modes)>0 {lines=append(lines,"Taviq-Modes: "+strings.Join(x.Modes,","))}
	if len(x.Models)>0 {lines=append(lines,"Taviq-Models: "+strings.Join(x.Models,","))}
	text:=strings.TrimRight(string(body),"\n")+"\n\n"+strings.Join(lines,"\n")+"\n"
	return os.WriteFile(message,[]byte(text),0644)
}


func diagnose() (map[string]any,error) {
	r,err:=root(); if err!=nil{return nil,err}
	hooksOut,_:=exec.Command("git","config","--get","core.hooksPath").Output()
	hooks:=strings.TrimSpace(string(hooksOut))
	checks:=map[string]bool{
		"git_repository":true,
		"hooks_path":hooks==".taviq/hooks",
		"prepare_commit_msg_hook":exists(filepath.Join(r,".taviq","hooks","prepare-commit-msg")),
		"runtime_writer":exists(filepath.Join(r,"scripts","set_runtime.py")),
		"commit_writer":exists(filepath.Join(r,"scripts","taviq_prepare_commit_msg.py")),
		"github_pr_summary":exists(filepath.Join(r,".github","workflows","taviq-basic.yml")),
	}
	core:=checks["hooks_path"]&&checks["prepare_commit_msg_hook"]&&checks["runtime_writer"]&&checks["commit_writer"]
	return map[string]any{"status":map[bool]string{true:"ready",false:"incomplete"}[core],"core_ready":core,"checks":checks},nil
}

func exists(path string) bool {_,err:=os.Stat(path);return err==nil}

func uniq(xs []string) []string {
	m:=map[string]bool{}; out:=[]string{}
	for _,x:=range xs {if x!=""&&!m[x]{m[x]=true;out=append(out,x)}}
	sort.Strings(out); return out
}

func main(){
	if len(os.Args)>=4 && os.Args[1]=="hook" && os.Args[2]=="prepare-commit-msg" {
		if err:=hook(os.Args[3]);err!=nil{fmt.Fprintln(os.Stderr,err);os.Exit(1)};return
	}
	fmt.Println("Taviq Go Core spike")
	fmt.Println("supported: hook prepare-commit-msg <message-file>")
}
