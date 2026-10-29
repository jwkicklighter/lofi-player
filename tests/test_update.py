"""Self-update tests; no network or playback dependencies required."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "lofi"


class UpdateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        for name in ("bash", "dirname", "basename", "readlink", "mktemp",
                     "head", "chmod", "mv", "rm", "cp"):
            (self.bin / name).symlink_to(shutil.which(name))
        self.target = self.root / "install with spaces" / "lofi"
        self.target.parent.mkdir()
        shutil.copy2(SCRIPT, self.target)
        self.payload = self.root / "payload"
        self.payload.write_text("#!/usr/bin/env bash\necho updated\n")
        self.env = dict(os.environ, PATH=str(self.bin), HOME=str(self.root),
                        PAYLOAD=str(self.payload))
        self.curl = self.bin / "curl"
        self.curl.write_text('''#!/bin/bash
printf '%s\\n' "$@" > "$HOME/curl.log"
while [[ $# -gt 0 ]]; do
  if [[ "$1" == -o ]]; then cp "$PAYLOAD" "$2"; exit; fi
  shift
done
exit 1
''')
        self.curl.chmod(0o755)

    def update(self, target=None):
        return subprocess.run([shutil.which("bash"), str(target or self.target),
                               "update"], env=self.env, text=True,
                              capture_output=True)

    def test_update_without_jq(self):
        result = self.update()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.target.read_bytes(), self.payload.read_bytes())
        self.assertIn(
            "https://github.com/jwkicklighter/lofi-player/releases/latest/download/lofi",
            (self.root / "curl.log").read_text())
        self.assertTrue(os.access(self.target, os.X_OK))
        self.assertFalse((self.root / ".config").exists())

    def test_relative_symlink(self):
        link = self.root / "lofi-link"
        link.symlink_to(self.target.relative_to(self.root))
        result = self.update(link)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(link.is_symlink())
        self.assertEqual(self.target.read_bytes(), self.payload.read_bytes())

    def test_invalid_downloads_preserve_script(self):
        original = self.target.read_bytes()
        for content in ("", "<html>error</html>", "#!/usr/bin/env bash\nif\n"):
            with self.subTest(content=content):
                self.payload.write_text(content)
                result = self.update()
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(self.target.read_bytes(), original)
                self.assertEqual(list(self.target.parent.glob(".lofi-update.*")), [])

    def test_network_failure_preserves_script(self):
        original = self.target.read_bytes()
        self.curl.write_text("#!/bin/bash\nexit 22\n")
        result = self.update()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.target.read_bytes(), original)
        self.assertEqual(list(self.target.parent.glob(".lofi-update.*")), [])


if __name__ == "__main__":
    unittest.main()
