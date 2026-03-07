# terminal-ify

A sleek Spotify client for your terminal. Control playback, browse your library, and search for music — all without leaving the command line.

![Python](https://img.shields.io/badge/python-3.10+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## Features

- Playback controls (play, pause, skip, previous, shuffle, repeat)
- Now Playing view with progress bar and album art (ASCII)
- Browse and play from your playlists, saved albums, and liked songs
- Search for tracks, albums, artists, and playlists
- Queue management
- Volume control
- Device switching
- Keyboard-driven UI with vim-style navigation

## Prerequisites

- Python 3.10+
- A Spotify Premium account (required for playback control)
- A Spotify Developer application (for API credentials)

## Setup

### 1. Create a Spotify App

1. Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new application
3. Set the redirect URI to `https://terminalify.343-guilty-spark.io/callback`
4. Note your **Client ID** and **Client Secret**

### 2. Install

```bash
pip install terminal-ify
```

Or install from source:

```bash
git clone https://github.com/frontsidebus/terminal-ify.git
cd terminal-ify
pip install -e .
```

### 3. Configure

Create a `.env` file in the project root with your Spotify credentials:

```
SPOTIPY_CLIENT_ID=your-client-id
SPOTIPY_CLIENT_SECRET=your-client-secret
```

### 4. Run

```bash
terminal-ify
```

On first launch, a browser window will open for Spotify authentication. After granting access, you're good to go.

## Infrastructure (AWS)

The OAuth callback runs on AWS Lambda behind API Gateway with TLS. To deploy:

```bash
cd infra
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your Spotify credentials
terraform init
terraform apply
```

After applying, Terraform outputs:
- **certificate_validation_records** — add these CNAMEs in Namecheap for ACM cert validation
- **custom_domain_target** — CNAME `terminalify.343-guilty-spark.io` to this value in Namecheap

## Keybindings

| Key | Action |
|-----|--------|
| `space` | Play / Pause |
| `n` | Next track |
| `p` | Previous track |
| `+` / `-` | Volume up / down |
| `s` | Toggle shuffle |
| `r` | Cycle repeat mode |
| `/` | Search |
| `1` | Now Playing |
| `2` | Playlists |
| `3` | Library |
| `4` | Search |
| `q` | Quit |
| `?` | Help |

## License

MIT
