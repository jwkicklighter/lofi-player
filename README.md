# lofi-player

Background audio from a YouTube live stream, controlled from the terminal.
Playback is [mpv](https://mpv.io) + [yt-dlp](https://github.com/yt-dlp/yt-dlp); `lofi` is a thin
wrapper that talks to mpv over its JSON IPC socket.

## Install

```sh
curl -fsSL https://github.com/jwkicklighter/lofi-player/releases/latest/download/install | bash
```

Supports macOS ([Homebrew](https://brew.sh) required), Arch Linux / Omarchy,
and Ubuntu. Installs missing dependencies (`mpv`, `yt-dlp`, `socat`, `jq`, `curl`)
and downloads `lofi` to `~/.local/bin`. Run as your regular user; Linux package
installation uses `sudo` and may prompt for your password. On Arch, installing
dependencies also performs a full system upgrade to avoid partial upgrades.

The installer adds the destination to your shell configuration for Bash, Zsh,
or Fish if needed. Open a new terminal afterward. To choose another location or
leave shell configuration unchanged:

```sh
curl -fsSL https://github.com/jwkicklighter/lofi-player/releases/latest/download/install | LOFI_INSTALL_DIR="$HOME/bin" bash -s -- --no-modify-path
```

Run `lofi update` to download the latest stable GitHub release without rerunning the
installer. This updates the script only, not its dependencies or your settings.
To inspect the installer first, download `install` and run
`bash install --help` or `bash install`. Ubuntu packages may lag behind upstream
`yt-dlp`; if YouTube playback breaks, you may need a newer `yt-dlp` release.

### Manual install (other operating systems)

On other Unix-like systems, install **Bash**, **mpv**, **yt-dlp**, **jq**,
**socat**, and **curl** using your system's package manager. Package names may
vary; if a package isn't available, follow its upstream installation instructions.
Python 3 can replace `socat` for mpv socket communication. Standard Unix utilities
such as `awk`, `sed`, and `seq` must also be available.

For example, on Fedora:

```sh
sudo dnf install bash mpv yt-dlp jq socat curl
```

Then download the script and make it executable (no root access needed):

```sh
mkdir -p "$HOME/.local/bin"
curl -fsSL https://github.com/jwkicklighter/lofi-player/releases/latest/download/lofi -o "$HOME/.local/bin/lofi"
chmod +x "$HOME/.local/bin/lofi"
```

If `~/.local/bin` isn't already on your PATH, add the following to your Bash or
Zsh startup file (`~/.bashrc` or `~/.zshrc`), then open a new terminal:

```sh
export PATH="$HOME/.local/bin:$PATH"
```

For Fish, run `fish_add_path "$HOME/.local/bin"` instead. Verify the installation
with `lofi channels`. Native Windows is not supported; use a Linux environment
with working audio, such as WSL with WSLg.

## Use

```sh
./lofi list                  # live streams from your channels, favorites first
./lofi start                 # resume the last stream (first run: top of the list)
./lofi start jazz            # first live stream whose title contains "jazz"
./lofi start 4               # 4th entry from `lofi list`
./lofi start 'https://www.youtube.com/watch?v=…'   # quote URLs in zsh
./lofi toggle                # play/pause (also: pause, resume)
./lofi vol +5 | ./lofi vol -5 | ./lofi vol 40
./lofi status                # {"text":"▶ 60%","class":"playing",...}
./lofi stop
./lofi update                # download the latest stable GitHub release
./lofi play                  # foreground: space, 9/0, q

./lofi channels              # your channels
./lofi add @ChillhopMusic    # also a channel URL, or the URL of one of its streams
./lofi remove @ChillhopMusic # also a number from `lofi channels`, or a name

./lofi favorite              # list favorites
./lofi favorite add          # favorite what's playing (or pass a number / title / URL)
./lofi favorite remove jazz
```

`start` while something is already playing switches streams in place.

When resuming, `lofi` checks that the last stream's URL is still live. If not, it looks
for a live stream with the same title on the same channel (streams sometimes restart
under a new URL), and tells you if that stream is gone.

## Publishing releases

Push a version tag on the commit you want to release:

```sh
git tag v1.0.0
git push origin v1.0.0
```

The release workflow runs syntax checks and tests on Linux and macOS, then
creates a draft GitHub release with `lofi` and `install` attached and publishes
it once both assets are uploaded. Release notes are generated automatically.
The workflow uses GitHub's built-in token; no additional secrets are needed.

Use `vMAJOR.MINOR.PATCH` for stable releases, or a suffix such as
`v1.1.0-beta.1` for prereleases. Prereleases are marked accordingly and excluded
from the stable `releases/latest/download/…` URLs. The first stable release must
be published before those install and update URLs will work.

## Files

- `~/.config/lofi/config.json`: channels and favorites (`$XDG_CONFIG_HOME` is respected)
  - `default_channels`: built-in channels (Lofi Girl). `lofi remove` sets `"hidden": true`
    on these instead of deleting them; `lofi add "Lofi Girl"` brings it back.
  - `channels`: channels you added.
  - `favorites`: stream titles, so a favorite survives its stream getting a new URL.
- `~/.local/state/lofi/last.json`: the last played stream (`$XDG_STATE_HOME` is respected)

Env overrides: `LOFI_CONFIG`, `LOFI_STATE`, `LOFI_VOLUME`, `LOFI_SOCKET`.

## Waybar (Omarchy)

```jsonc
"custom/lofi": {
  "exec": "~/dev/lofi-player/lofi status",
  "return-type": "json",
  "interval": 2,
  "on-click": "~/dev/lofi-player/lofi toggle",
  "on-click-right": "~/dev/lofi-player/lofi stop",
  "on-click-middle": "~/dev/lofi-player/lofi start",
  "on-scroll-up": "~/dev/lofi-player/lofi vol +5",
  "on-scroll-down": "~/dev/lofi-player/lofi vol -5"
}
```

For media keys and `playerctl`, install `mpv-mpris`. mpv then shows up as an MPRIS player.
