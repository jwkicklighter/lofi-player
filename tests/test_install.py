"""Installer integration tests with isolated HOME and mocked package managers.

Run: python3 -m unittest discover -s tests
"""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


INSTALLER = (Path(__file__).resolve().parents[1] / "install").read_text()


class InstallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.home = self.root / "home with ' quote"
        self.home.mkdir()
        self.env = dict(os.environ, HOME=str(self.home), PATH=str(self.bin),
                        SHELL="/bin/bash", LOG=str(self.root / "log"))
        for name in ("bash", "mkdir", "mktemp", "head", "chmod", "mv", "rm",
                     "dirname", "grep", "cp", "cat"):
            (self.bin / name).symlink_to(shutil.which(name))
        for name in ("mpv", "yt-dlp", "socat", "jq"):
            self.mock(name, "exit 0")
        self.mock("uname", "echo Darwin")
        self.mock("curl", '''
printf '%s\\n' "$@" >> "$LOG"
while [[ $# -gt 0 ]]; do
  if [[ "$1" == -o ]]; then
    printf '#!/usr/bin/env bash\\necho installed\\n' > "$2"
    exit
  fi
  shift
done
exit 1
''')

    def mock(self, name, body):
        path = self.bin / name
        path.write_text("#!/bin/bash\nset -eu\n" + body + "\n")
        path.chmod(0o755)

    def run_install(self, *args, source=INSTALLER):
        # Pass the installer through stdin, just like curl | bash.
        return subprocess.run([shutil.which("bash"), "-s", "--", *args],
                              input=source, text=True, env=self.env,
                              capture_output=True)

    def test_install_and_idempotent_path(self):
        for _ in range(2):
            result = self.run_install()
            self.assertEqual(result.returncode, 0, result.stderr)
        target = self.home / ".local/bin/lofi"
        self.assertTrue(os.access(target, os.X_OK))
        self.assertIn(
            "https://github.com/jwkicklighter/lofi-player/releases/latest/download/lofi",
            (self.root / "log").read_text())
        config = self.home / ".bash_profile"
        self.assertEqual(config.read_text().count("# lofi-player"), 1)
        result = subprocess.run([shutil.which("bash"), "-c",
                                 'source "$HOME/.bash_profile"; command -v lofi'],
                                env=self.env, capture_output=True, text=True)
        self.assertEqual(result.stdout.strip(), str(target))

    def test_no_modify_path(self):
        result = self.run_install("--no-modify-path")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.home / ".bash_profile").exists())

    def test_failed_download_preserves_install_and_cleans_up(self):
        self.assertEqual(self.run_install().returncode, 0)
        target = self.home / ".local/bin/lofi"
        original = target.read_bytes()
        self.mock("curl", "exit 22")
        self.assertNotEqual(self.run_install().returncode, 0)
        self.assertEqual(target.read_bytes(), original)
        self.assertEqual(list(target.parent.glob(".lofi-install.*")), [])

    def test_package_managers(self):
        for platform, distro, manager, expected in (
            ("Darwin", "", "brew", "install mpv"),
            ("Linux", "arch", "pacman", "-Syu --needed --noconfirm mpv"),
            ("Linux", "ubuntu", "apt-get", "install -y mpv"),
        ):
            with self.subTest(platform=platform, distro=distro):
                (self.bin / "mpv").unlink()
                self.mock("uname", f"echo {platform}")
                release = self.root / "os-release"
                release.write_text(f"ID={distro}\n")
                self.mock(manager, '''
echo "$*" >> "$LOG"
cp "$HOME/../dependency" "${PATH}/mpv"
''')
                self.mock("sudo", 'exec "$@"')
                dependency = self.root / "dependency"
                dependency.write_text("#!/bin/bash\nexit 0\n")
                dependency.chmod(0o755)
                result = self.run_install(source=INSTALLER.replace(
                    "/etc/os-release", str(release)))
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(expected, (self.root / "log").read_text())

    def test_unsupported_os_and_bad_options(self):
        self.mock("uname", "echo FreeBSD")
        self.assertNotEqual(self.run_install().returncode, 0)
        self.assertNotEqual(self.run_install("--unknown").returncode, 0)
        self.assertEqual(self.run_install("--help").returncode, 0)


if __name__ == "__main__":
    unittest.main()
