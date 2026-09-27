import importlib.util, subprocess, tempfile, unittest
from pathlib import Path

P=Path(__file__).parents[1]/"scripts"/"install_basic.py"
S=importlib.util.spec_from_file_location("installer",P); M=importlib.util.module_from_spec(S); S.loader.exec_module(M)

def git(repo,*args):
    return subprocess.run(["git","-C",str(repo),*args],text=True,capture_output=True)

class InstallerTests(unittest.TestCase):
    def repo(self,d):
        r=Path(d); subprocess.check_call(["git","init",str(r)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); return r

    def test_install_uninstall_restores_previous_hooks_path(self):
        with tempfile.TemporaryDirectory() as d:
            r=self.repo(Path(d)/"repo")
            subprocess.check_call(["git","-C",str(r),"config","core.hooksPath",".existing-hooks"])
            M.install(r)
            self.assertEqual(git(r,"config","--get","core.hooksPath").stdout.strip(),".taviq/hooks")
            self.assertEqual((r/".taviq"/"install-state").read_text(),".existing-hooks")
            M.uninstall(r)
            self.assertEqual(git(r,"config","--get","core.hooksPath").stdout.strip(),".existing-hooks")

    def test_uninstall_removes_taviq_setting_when_no_previous_path(self):
        with tempfile.TemporaryDirectory() as d:
            r=self.repo(Path(d)/"repo")
            M.install(r); M.uninstall(r)
            self.assertNotEqual(git(r,"config","--get","core.hooksPath").returncode,0)
            self.assertFalse((r/".taviq"/"hooks"/"prepare-commit-msg").exists())

    def test_reinstall_preserves_original_hooks_path(self):
        with tempfile.TemporaryDirectory() as d:
            r=self.repo(Path(d)/"repo")
            subprocess.check_call(["git","-C",str(r),"config","core.hooksPath",".original"])
            M.install(r); M.install(r); M.uninstall(r)
            self.assertEqual(git(r,"config","--get","core.hooksPath").stdout.strip(),".original")

if __name__=="__main__": unittest.main()
