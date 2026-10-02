# lofi-player

Background audio from a YouTube live stream, controlled from the terminal.
Playback is [mpv](https://mpv.io) + [yt-dlp](https://github.com/yt-dlp/yt-dlp); `lofi` is a thin
wrapper that talks to mpv over its JSON IPC socket.

## Install

```sh
# macOS
brew install mpv yt-dlp socat jq
# Arch / Omarchy
sudo pacman -S mpv yt-dlp socat jq
```

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
