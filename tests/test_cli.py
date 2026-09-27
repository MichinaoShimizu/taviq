import subprocess, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).parents[1]
CLI=ROOT/"scripts"/"taviq"

class CliTests(unittest.TestCase):
    def repo(self,d):
        r=Path(d)/"repo"; subprocess.check_call(["git","init",str(r)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); return r

    def run(self,*args):
        return subprocess.run(["python3",str(CLI),*map(str,args)],text=True,capture_output=True)

    def test_install_doctor_uninstall_command_contract(self):
        with tempfile.TemporaryDirectory() as d:
            r=self.repo(d)
            x=self.run("install","--repo",r); self.assertEqual(x.returncode,0,x.stderr)
            # This external test repo intentionally lacks Taviq scripts, so doctor must report incomplete.
            x=self.run("doctor","--repo",r,"--json"); self.assertNotEqual(x.returncode,0)
            self.assertIn('"core_ready": false',x.stdout)
            x=self.run("uninstall","--repo",r); self.assertEqual(x.returncode,0,x.stderr)

    def test_help_exposes_stable_commands(self):
        x=self.run("--help")
        self.assertEqual(x.returncode,0)
        for command in ("install","uninstall","doctor"): self.assertIn(command,x.stdout)

if __name__=="__main__": unittest.main()
