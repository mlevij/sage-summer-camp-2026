# Sage Grande Workshop Prep — Technical Notes

---

## Session: 2026-07-13

### Phase 1: Linux & SSH fundamentals
**Working with files:** `pwd`, `ls`, `mkdir`, `cd`, `cat`, `echo "text" > file` (write via redirection), `cp`, `mv` (copy/rename — same command does both), `rm` (no undo/recycle bin).

**Reading/searching files:** `head`, `tail`, `less` (the `/pattern` search gotcha — search starts from current cursor position, not file start; fix with `g` to jump to top first), `grep` (name origin: `g/re/p` from the old `ed` editor), regex anchors `^`/`$`.

**Pipes/redirection:** `|` (e.g. `history | grep mkdir` — note the grep command itself can show up in its own search), `>` (overwrite) vs `>>` (append).

**Processes/permissions:** `ps`, `top` (load average, memory, process states R/S), `kill` (tested against `sleep 300 &`). Permissions via `chmod +x` on a hand-written script — hit a real nested-quoting bug where `echo 'echo "the script ran"' >> file` didn't write what was intended; fixed by using `nano` instead of debugging the quoting.

**SSH config walkthrough:** Read through `~/.ssh/config` line by line — the two `Host` blocks, `ProxyCommand`'s bastion-host pattern (uses `sed "s/waggle-dev-node-//"` to strip a prefix), `IdentitiesOnly` (avoids untargeted key-guessing that risks server-side lockout), `StrictHostKeyChecking no` (reasonable trade-off specifically for a jump-host-mediated many-node fleet, not a general best practice).

**Live connection test:** `ssh waggle-dev-node-V030` (Sage's own example node). Original `sage_key` passphrase was forgotten — 3 failed attempts, connection closed by the server (SSH's own brute-force protection). Generated a new ed25519 key pair (same filename, no config changes needed), registered the new public key on Sage's portal. Portal UI gave no visible save confirmation and didn't list any keys — resolved empirically by retrying the SSH connection directly: reached the gateway successfully, cleanly denied access to V030 specifically ("You do not have access to node V030") rather than any auth/connection error — confirms the new key registered correctly and the full auth chain works end to end.

**Real node access — H019** (device ID `00004CBB4701CE9D`). First connection attempt hung indefinitely after passphrase prompts. Retry failed with `Could not resolve hostname beekeeper.sagecontinuum.org: Temporary failure in name resolution` — diagnosed as a WSL2 DNS/networking issue (confirmed via `ping google.com` also failing). Fixed with `wsl --shutdown` from PowerShell, then reopened Ubuntu fresh — DNS resolved correctly and the connection succeeded. Confirmed genuinely on remote hardware (not just the jump host): hostname changed entirely, kernel string shows `aarch64`/`tegra` (ARM/NVIDIA Jetson-class edge hardware), OS banner shows a minimized Ubuntu image typical of unattended edge deployments.

**Live node exploration (read-only) on H019:**
- `df -h` / `free -h`: 3.6 TB storage, 122 GB RAM — Sage field nodes are genuinely powerful machines, not tiny low-power sensors.
- `docker ps` / `docker images`: both empty, node genuinely idle.
- `which pluginctl`: found at `/usr/bin/pluginctl` (Sage's deployment tool, per-user kubeconfig at `~/.kube/config`).
- `pluginctl ps`: permission error (`pods is forbidden... in namespace "default"`) — same "no access yet" pattern as V030, likely tied to workshop-specific namespace provisioning not yet in place.
- `nvidia-smi`: GPU is an NVIDIA Thor chip (explains the `sgt-thor-...` hostname), CUDA 13.0, idle (0% util).
- `who`: two users connected, both showing as `127.0.0.1` — demonstrates the bastion/ProxyCommand pattern making all connections appear local by the time they reach the node.
- `uptime`: 13 days continuous, no reboot.

### Phase 2: Docker & Containers
Installed via `sudo apt install docker.io` (chose over `snap install` due to known WSL2 reliability quirks with snap). Fixed a Docker-socket permission error with `sudo usermod -aG docker $USER` — required a fresh terminal session, since group changes don't apply retroactively to an already-open shell.

- `docker run hello-world` — first successful pull+run, demonstrates client/daemon architecture.
- `docker run -d ubuntu sleep 300/600`, `docker ps` / `docker ps -a`, `docker stop` — full container lifecycle. A container that finishes naturally shows `Exited (0)`; one stopped manually via `docker stop` shows `Exited (137)` (128+9, SIGKILL).
- Wrote a Dockerfile (`FROM python:3.12-slim` / `COPY hello.py .` / `CMD [...]`), built with `docker build -t my-first-image .`.
- Volumes: `docker run --rm -v ~/docker-practice:/app ubuntu ls /app` — proved a container can see live local files without rebuilding.
- Ports: `docker run -d -p 8080:80 --name my-web-test nginx` + `curl localhost:8080` — got real HTML back, full request round-trip confirmed.

### Phase 3: Running AI Models Locally
Installed Ollama via its official install script (`curl -fsSL https://ollama.com/install.sh | sh`) — hit a missing dependency (`zstd`, fixed via apt). Installed as a systemd service, API at `127.0.0.1:11434`.

- `ollama pull llama3.2` — downloaded (~2GB).
- `ollama run llama3.2` — first interactive chat with a fully local model.
- Python integration: `pip` not installed initially (`sudo apt install python3-pip`), then `pip install ollama` blocked by PEP 668 ("externally-managed-environment"). Fixed with a venv (`python3 -m venv venv`, `source venv/bin/activate`), then `pip install ollama` succeeded inside the isolated environment.
- Wrote `query.py` using the `ollama` Python library (`ollama.chat(model=..., messages=[...])`) — full local-Python-to-local-LLM loop confirmed working.
- Hugging Face `transformers`: `pipeline("image-classification")` produced the "using a pipeline without specifying a model name and revision" warning — expected, not a bug: with no model named, HF auto-picks a default (here `google/vit-base-patch16-224`) that can silently change over time since it's unpinned. Fix if needed: pass `model=` and `revision=` explicitly.

---

## Session: 2026-07-17

### Phase 3 quantization comparison
Checked `ollama list`: `llama3.2:latest` (2.0 GB, quantized) and `llama3.2:3b-instruct-fp16` (6.4 GB, full precision) — same 3B model at two precisions, a direct size/quality comparison. Full-precision version deemed worth using.

### Phase 4: `sage-data-client` install
`pip install sage-data-client` hit the same PEP 668 error as Phase 3 — venv wasn't active. The Phase 3 venv turned out to live at `~/docker-practice/venv` (created while inside the Docker practice folder), not in the home directory — located via `find ~ -iname "pyvenv.cfg"`.

**Standing rule going forward:** always confirm the venv is active before any `pip install` in this environment, so nothing installs system-wide by accident.

**Real queries run** against Sage's public API (no account needed):
- `query(start='-1h', filter={'name': 'env.temperature'})` — 17,696 rows, live data from node `W02C`.
- `query(start='-1h', filter={'vsn': 'W02C'})` then `df['name'].unique()` — 163 distinct measurement types from a single node, including `env.count.car`/`env.count.person`/`env.count.traffic_light` (live object-detection AI output from the node's camera) and `traffic.state.*` (derived traffic analytics).

**BirdNET/Waggle plugin reference:** Cornell's Merlin app itself has no embeddable SDK, but the underlying **BirdNET** model lineage has a real existing Sage/Waggle plugin — [`BirdNET_Lite_Plugin`](https://github.com/dariodematties/BirdNET_Lite_Plugin), plus a more general [`plugin-yamnet`](https://github.com/waggle-sensor/plugin-yamnet) for broader sound classification.

**Sanity checks:** `docker run hello-world` and `ollama run llama3.2 "test"` both confirmed still working.

---

## Session: 2026-07-18

### Pre-arrival checklist / node access
- SSH access test (`ssh <username>@waggle-dev-node-h037 hostname`) confirmed working on the first attempt; H02E also already accessible.
- **Node access is per-node**: H019, H037, and H02E are three separate physical nodes — access to one doesn't carry over to another, even though the same Sage account/SSH key works for all.

### Hermes install on H02E — fully completed and verified
- `curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash` — clean install. Sudo prompts (ripgrep, build tools) appeared for an account with no real password (workshop accounts are key-based-SSH-only) — installer gracefully continued past both, since sudo is optional for Hermes.
- Setup wizard: **Blank Slate** mode (workshop's guide calls for this since the pre-built Sage profile installs on top right after). Terminal backend set to **local** (Thor uses Podman, not Docker, so local avoids that dependency).
- **Sage profile install**: caught a discrepancy in the original guide — its `git clone` pointed to a personal fork (`FranciscoLozCoding/summer-camp-2026`) instead of the canonical `waggle-sensor/summer-camp-2026`. Cloned the canonical repo instead (confirmed via presence of the expected `hermes-profile/` directory, `sage` v1.0.7 installed cleanly). `hermes doctor` came back fully green.
- **NVIDIA NIM + glm-5.2 configuration**: confirmed the exact model identifier via a live search (`z-ai/glm-5.2`, base URL `https://integrate.api.nvidia.com/v1`). `hermes model` wizard configured cleanly first try.
- **Verification test**: launched inside `tmux` (`tmux new -s hermes` → `hermes`), asked it to self-identify. Response correctly reported `z-ai/glm-5.2` via the `nvidia` provider, correctly attributed GLM to Zhipu AI, correctly distinguished the Hermes Agent shell (Nous Research) from the underlying LLM.

### SSH/tmux/Hermes exit mechanics
- `ssh mlevij@waggle-dev-node-h02e` to connect, `Ctrl-b` `d` to detach from tmux without killing the session, `exit`/`logout` at a plain bash prompt to close the SSH connection, `tmux attach -t hermes` to resume later.
- `/quit` (alias `/exit`) is Hermes's real exit command. Plain `exit` typed while inside the Hermes chat itself does **not** close it — Hermes just treats untyped text as a chat message.

---

## Session: 2026-07-20

### Sage node + Hermes login — verified end to end
The tmux session from 07-18 hadn't survived (likely a reboot) — `tmux ls` on H02E returned "no server running." Redid the flow live:
- `ssh mlevij@waggle-dev-node-h02e` (the post-quantum key exchange warning at connect time is informational only, not a real issue).
- `tmux new -s hermes` → `hermes`.

**tmux mouse-scroll quirk, fixed:** mouse wheel inside tmux was scrolling through Hermes's input history instead of the conversation view — tmux translates unmodified wheel scroll into arrow-key sequences, which Hermes reads as history navigation. Fixed by enabling tmux mouse mode: `Ctrl-b` `:` then `set -g mouse on`. (Alternative for one-off scrollback without changing settings: `Ctrl-b` `[` to enter copy mode, `q` to exit.)

### Hermes agentic test: sensor inventory on H02E
Asked Hermes "what sensors are on this device" — it chained ~20+ real shell commands (USB, `/etc/waggle`, `media-ctl` topology, hwmon, one sudo timeout it gracefully worked around):
- **Onboard**: Jetson AGX Thor SoC, PWM fan+tach, tmp451 board temp, soctherm_oc, ina238/ina3221 power monitors, ALSA audio (no external mic captured), 4 CAN bus interfaces (down), 6 input event devices.
- **External/USB**: Bluetooth radio, USB hubs, an unidentified FT232 USB-serial device on `/dev/ttyUSB0` (possible GPS, unconfirmed — `cat /dev/ttyUSB0` would show NMEA sentences if so), RTL8153 Ethernet, a USB flash drive.
- **Network**: `wg-sage` WireGuard tunnel up (node's link to Beehive); most other interfaces down/no-carrier.
- **Notable finding**: `node-manifest-v2.json` reports an empty `sensors` array — no soil moisture, weather, or camera sensors registered on H02E. No `/dev/video*` either (no camera probed).

### Class assignment: `sage_data_client` queries
1. **Avg temp, W021, last hour** — `query(start='-1h', filter={'name': 'env.temperature', 'vsn': 'W021'})` → 54.52°C, flagged as unusually hot (see W06C investigation below for a parallel case). Attempting to SSH directly into W021 gave `Permission denied (publickey)` — portal visibility and SSH access are separate permission layers.
2. **Latest temp, all nodes, last 5 min** — script pattern: `groupby('meta.vsn').last()`.
3. **Download a data-API image via curl** — completed, see below.

### Image download via curl — real debugging chain
- **Security incident**: a first download attempt used an NVIDIA API key mistakenly used as the Sage portal password (`-u mlevij:nvapi-...`). Key was regenerated on NVIDIA's Build portal as a precaution.
- **`-O` vs `-o` confusion**: `-O` (capital, no argument) auto-names the file from the URL; `-o <path>` (lowercase) lets you pick the destination/name — they aren't interchangeable the way they were first tried.
- **Root cause of repeated silent 0-byte/corrupted-file failures**: `storage.sagecontinuum.org` returns an HTTP 302 redirect (`content-length: 0`) to `nrdstor.nationalresearchplatform.org`, with a signed `?authz=<JWT>` token embedded in the redirect URL. Plain `curl -O`/`-o` does not follow redirects by default, so every attempt silently saved the empty 302 response. Diagnosed via `curl -i` (headers only, no save) instead of guessing further. **Fix: add `-L`.**
- **WSL2 vs Windows filesystem**: `/mnt/c/...` is the real Windows filesystem, accessible both ways; `/home/mlevij`/`~` is WSL2-only and invisible to Windows Explorer/OneDrive.

Final working pattern:
```
cd "/mnt/c/Users/mlevij/OneDrive - Colostate/Levi/Sage"
curl -L -u mlevij:<token> -O "https://storage.sagecontinuum.org/api/v1/data/imagesampler-mobotix-2689/sage-imagesampler-mobotix-0.3.7/000048b02d3ae335/1784574008590260388-sample.jpg"
```

### Investigation: why was W06C's temperature reading so hot?
- Listed all measurement names published by W06C — found two temperature-relevant names: `env.temperature` (official Waggle measurement) and `iio.in_temp_input` (raw Linux IIO/sysfs sensor file, `/sys/bus/iio/devices/.../in_temp_input`).
- `iio.in_temp_input`'s raw values were in the tens-of-thousands (e.g. 62520) — standard Linux IIO/hwmon convention of milli-°C, not whole degrees (÷1000 → plausible range).
- Values alternated between two clusters (~62.5° / ~29.5°) — traced via `meta` columns to two genuinely distinct sensors publishing under the identical measurement name: `wes-iio-bme280` at `meta.zone = core` (mounted in the compute enclosure, near electronics) vs. `wes-iio-bme680` at `meta.zone = shield` (a radiation shield, the standard technique for housing a temp sensor so it reads true ambient air rather than solar/electronics-heated air).
- Confirmed with `groupby('meta.zone')`: **core = 61.09°C (std 0.93)**, **shield = 28.11°C (std 1.04)** — two tight, well-separated distributions. The shielded value lines up with `env.temperature`'s own tail, confirming that's the trustworthy ambient measurement; a naive unfiltered average blends two physically different sensor placements over 30° apart.

### 30-day precip table for W06C
Used `env.raingauge.total_acc` (a cumulative counter, so daily precip = diff of consecutive daily-last values, not the raw value itself). First version used `.fillna(daily.iloc[0])` for the first day, which produced a misleading value from the raw cumulative total with no prior day to diff against — fixed by switching to `.dropna()` instead, correctly starting the table from the first day a real diff exists.

**Units check**: no `meta.units` field exists in the API response. Traced the hardware via `meta.task = wes-raingauge` → confirmed via the `plugin-raingauge` GitHub repo this is a **Hydreon RG-15 optical rain gauge**, which supports configurable mm/inches output at the device level — not confirmable from API metadata alone. mm concluded highly likely based on value magnitude, but not fully confirmed without the device's actual field config.

### Edge app tutorial: mean-color plugin, built and deployed
Worked through Sage's "Creating an edge app" / "Testing an edge app" tutorial:
- **Cookiecutter scaffold**: `pip3 install --upgrade cookiecutter`, then `cookiecutter gh:waggle-sensor/cookiecutter-sage-app` with `kind = 4` (tutorial) → generated `main.py`, `requirements.txt`, `Dockerfile`, `sage.yaml`.
- **Recurring mistake**: pasting multi-line Python code directly at the bash prompt instead of into a file first (bash tries to interpret `import`/`from`/etc. as shell commands). Standing rule: Python code goes into a file via `nano`, never typed straight at `$`.
- **No live camera in WSL2**: `Camera()` (default device index 0) failed — `/dev/video0` doesn't exist because WSL2 has no automatic webcam passthrough. Fixed by reading pywaggle's actual installed source (`waggle/data/vision.py`) and confirming `Camera(device=...)` accepts a `Path` to a static image file (resolves via `resolve_device_from_path`, then calls `cv2.VideoCapture` on it — OpenCV can open a single image as a one-frame "video"). Used a static test JPEG for local testing.
- **BGR vs RGB**: raw `cv2.imread` gives BGR; pywaggle's `Camera` defaults to RGB (`format=RGB`) and converts internally.
- **`plugin.publish()` type restriction**: only accepts a single `int`/`float`/`str`, not a NumPy array — `mean_color` (three channel means) had to be split into three separate `plugin.publish()` calls (`env.mean_color.r/.g/.b`), matching the one-scalar-per-measurement-name pattern seen in real Sage data.
- **Local test loop confirmed working**: `PYWAGGLE_LOG_DIR=test-run python3 main.py` → `test-run/data.ndjson` correctly logged all three published metrics. `snapshot.save()` + `plugin.upload_file()` confirmed working too (`test-run/uploads/`).
- **Git identity missing** on first commit attempt: "empty ident name" — fixed with `git config --global user.email/user.name` (separate one-time fix per machine, unrelated to GitHub login).
- **`gh` CLI not installed** in this WSL2 environment — installed via `sudo apt install gh`, then `gh auth login` (browser device-code flow).
- Pushed to `github.com/mlevij/app-tutorial` (public, `master`).
- **Node deployment**: SSH'd into H02E, `git clone https://github.com/mlevij/app-tutorial`, `sudo pluginctl build .` → "Successfully built plugin", image `10.31.81.1:5000/local/app-tutorial`. (This step was flagged beforehand as the most likely to hit a `pluginctl` namespace/permission wall, per an earlier H019 `pluginctl ps` "forbidden" error — it didn't.)

Run/publish-to-cloud verification was not yet done this session — completed the following session (2026-07-21).

---

## Session: 2026-07-21

### tmux "duplicate session" — resolved
`tmux new -s hermes` on H02E returned `duplicate session: hermes`. Confirmed via `hostname` this was the same host as the previous session — tmux sessions persist across SSH disconnects by design, so `hermes` was simply the still-running session from before. Resolved with `tmux attach -t hermes` instead of creating a new one.

### NVIDIA API key reconfigured in Hermes
The NVIDIA API key had been rotated (07-20 exposure incident), leaving Hermes's `nvidia` provider config stale.
- Exited Hermes chat with `/quit`, then ran `hermes model` — the correct CLI command for reconfiguring an already-active provider (the in-chat `/model` slash command is for switching between already-configured models, not updating credentials).
- Provider picker showed NVIDIA NIM already active (`z-ai/glm-5.2`). Re-selecting it dropped into its existing config screen with a `[K]eep / [R]eplace / [C]lear` prompt.
- Chose **R**, pasted the new key, got `API key updated.` Accepted the default base URL unchanged.
- Re-ran the self-identify test — correctly reported `z-ai/glm-5.2` via the NVIDIA provider, correctly identified itself as "Wisp," a Hermes Agent (Nous Research), correctly distinguished agent shell from underlying LLM.

### tmux session died mid-session, re-created
A plain `exit` closed the SSH connection entirely (rather than just exiting Hermes), which killed the tmux session along with it (tmux tears down a session once its one pane's shell process exits). `tmux attach -t hermes` then returned `[exited]`. Reconnected and started a fresh `tmux new -s hermes` — no lasting harm, since nothing had been running that needed to persist.

### Edge app tutorial: run/publish verification, completed
First `pluginctl run` attempt scheduled successfully but sat in `"Pending"` state repeatedly — traced to a workshop-wide network issue affecting image pull/registry access that day, unrelated to the build itself (`pluginctl build` had already succeeded cleanly on 07-20).

Once the network issue cleared, retried and worked through several more real issues:
- **Stale pod blocking re-run**: a second `pluginctl run` attempt failed with a Kubernetes `Forbidden` error ("pod updates may not change fields other than image/tolerations/..."). The earlier stuck-Pending attempt had left a real pod object behind under the same name, and Kubernetes won't allow most fields to be changed on an existing pod, only recreated. `pluginctl ps` and plain `pluginctl rm app-tutorial` both came back `Forbidden`/"cannot list/delete pods" — a real RBAC restriction on the account (same pattern as the H019 `pluginctl ps` restriction from 07-13). **Fix: `sudo pluginctl rm app-tutorial`** succeeded where the unprivileged version didn't, cleanly terminating the stuck pod.
- **Root cause of the next failure**: after clearing the stale pod, the container crashed with `RuntimeError: unable to open video capture for device '/app/sample.jpg'`. Traced to the 07-20 tutorial code using a hardcoded WSL2-only path (`/mnt/c/Users/mlevij/Desktop/...`) that doesn't exist on H02E, since `main.py` had been pushed to GitHub and cloned onto the node as-is. Fixed by switching to a relative path (`Path("sample.jpg")`) and `scp`-ing the same test image directly onto the node (`scp <local-path> mlevij@waggle-dev-node-h02e:~/app-tutorial/sample.jpg`) so it'd be picked up by the Dockerfile's `COPY . .` step.
- **Near-misses caught along the way**: a rebuild attempt run from `~` instead of `~/app-tutorial` caused `pluginctl build .` to silently fail to find a Dockerfile, and `run` then relaunched the old broken image; a first `scp` attempt was assumed done but never actually completed — caught via `ls -la` showing "No such file or directory" before wasting another build cycle.
- **Confirmed working**: after the fix, `pluginctl run` completed almost instantly (one-shot script, not a persistent service) rather than hanging on "Pending." `pluginctl logs`/`ps` immediately returned "not found" afterward — expected, since the pod finishes and is cleaned up fast; the real verification came from the public data API:
  ```
  curl https://data.sagecontinuum.org/api/v1/query -d '{"start": "-10m", "filter": {"task": "app-tutorial", "vsn": "H02E"}}'
  ```
  Confirmed real published data: `env.mean_color.r/g/b` values plus an `upload` entry with a real snapshot URL on `storage.sagecontinuum.org`. (An unfiltered query also returns other workshop participants' overlapping `app-tutorial` publishes from other nodes — add the `vsn` filter to isolate one node's own result.)

### Switched from static test image to a live RTSP camera feed
Sage staff circulated an updated list of real camera streams to use in place of the tutorial's default `Camera("left")`, e.g. `Camera("rtsp://<host>:<port>/profile1/media.smp")`.
- Updated `main.py`'s `Camera(device=...)` line to the RTSP URL as a **plain string**, not wrapped in `Path(...)` — `Path()` is for local files, not stream URLs; a first attempt still had the `Path()` wrapper and needed correcting.
- The camera's RTSP URL embeds an admin password in plain text (`rtsp://user:pass@host:port/...`) — confirmed with workshop staff this is an intentionally shared, low-stakes demo credential before hardcoding it and pushing to a public repo.
- Editing `main.py` via VS Code's Remote-SSH extension was attempted as an alternative to `nano`, but never actually connected to H02E — it opened/created an unrelated, empty local folder on the laptop itself instead (confirmed by the shell prompt showing the local hostname, not H02E's). Reverted to plain `nano`, which worked without issue.
- A `sed`-based non-interactive edit was also offered (with `set +H` first, since the password's `!!` triggers bash history expansion in an interactive shell) as an alternative to opening an editor at all — not used in the end, but a viable one-liner approach for scripted edits when a value contains shell-special characters.
- Rebuilt and reran (`sudo pluginctl rm` → `build` → `run`), verified via the same filtered data-API query: real published values confirming the plugin is now genuinely pulling from the live camera instead of a static test file.

### GitHub push from H02E — auth failure, worked around
`git commit` on H02E succeeded, but `git push` failed repeatedly on GitHub authentication (no working credential helper/token configured on the node, separate from the Sage SSH key used for node access itself). Worked around by editing the file directly via GitHub's web editor instead of resolving node-side git auth. Still outstanding: set up real push access from H02E (e.g. `gh auth login` or a credential helper) to avoid this detour for future edits.

---

## Session: 2026-07-23

### H037 assigned; VS Code Remote-SSH fought and eventually abandoned in favor of plain terminal
Workshop assigned node **H037** (same Jetson AGX Thor hardware family as H02E, confirmed via `uname -a` — `6.8.12-tegra`, `aarch64`). User wanted to use VS Code instead of a bare terminal this time (matches everyone else at the workshop) — real troubleshooting saga, same root cause as the H02E Remote-SSH failure noted above (07-21 session):
- Plain `ssh mlevij@waggle-dev-node-h037 hostname` worked immediately (as expected, same key/gateway setup as H02E/H019) — confirms this was never a node-access problem.
- VS Code's Remote-SSH extension, even from inside a **WSL: Ubuntu**-connected window, still runs as a Windows-side/local extension and doesn't automatically read WSL's `~/.ssh/config` (where the working bastion `ProxyCommand` setup actually lives) — it defaults to the Windows-side config instead, hence "could not resolve hostname" for `waggle-dev-node-h037` (not a real DNS name, only resolvable via the config's proxy).
- Fix applied: set `remote.SSH.configFile` to the WSL path via UNC (`\\wsl.localhost\Ubuntu\home\mlevij\.ssh\config` — confirmed to exist first via Windows Explorer address bar, since `\\wsl$\...` is the older/alternate form and not guaranteed on every Windows build), specifically under the **User** settings tab (not the "Remote [WSL: Ubuntu]" tab, which the Settings UI defaults to when you're WSL-connected and edit settings there — the Remote-SSH extension doesn't read that scope).
- Still failed after that fix too ("could not resolve hostname" again) — ran out of appetite to keep debugging and **fell back to a plain terminal inside VS Code's integrated terminal panel** (`ssh mlevij@waggle-dev-node-h037`), which works fine and was good enough. Full GUI remote-window experience (file browser on the node, etc.) never actually achieved this session — worth revisiting later if it becomes worth the time investment, but not blocking.

### Python environment set up on H037
- `python3 --version` → 3.12.3, pip 24.0 already present at `/usr/bin/python3`.
- Learned lesson applied proactively (from the earlier WSL2 PEP 668 incident, 07-17 session): created a venv **before** installing anything — `python3 -m venv ~/df-venv` → `source ~/df-venv/bin/activate`. Avoided the externally-managed-environment error entirely.
- `pip install neonutilities` succeeded cleanly — all dependencies (`duckdb`, `pandas`, `pyarrow`, `h5py`, `pyproj`, etc.) had real `aarch64` prebuilt wheels available, nothing had to compile from source. `neonutilities` has no `__version__` attribute (minor package quirk, not a failure — `import neonutilities` succeeding is the real check).
- Disk: 3.6TB total, 3.3TB free. Memory: 122GB total, 55GB "available" (the number that matters, after reclaimable cache). No swap. Plenty of headroom for this work.
- NEON API token moved onto the node the simple way — opened the token file locally in Notepad, copied the value, then on H037: `cat > ~/.neon_token` (paste token, Enter, `Ctrl+D` to save) — avoided fighting `scp`/OneDrive path issues between Windows/WSL/node.

### Orthorectified camera imagery (AOP) — explored, deliberately dropped
Original idea: NEON's Airborne Observation Platform, `DP3.30010.001` (10cm RGB orthomosaic), for the same 2021-2026 window as the soil moisture pull. **User's own conclusion, before any code was written**: AOP is a once-a-year-ish flyover per site — nowhere near enough temporal density to be useful for a continuous 5-year comparison the way the 30-min soil moisture data is. Same sparsity problem would apply to AOP's spectrometer-derived vegetation indices (`DP3.30026.001`: NDVI/EVI/ARVI/PRI/SAVI/NDLI/NDNI — confirmed NEON has no dedicated LAI product in that set). Dropped in favor of NEON's in-situ PhenoCam instead, which actually matches the soil moisture data's continuous cadence and site.

### PhenoCam (DP1.00033.001) investigation — real, useful findings
Confirmed via NEON's own `/api/v0/data/DP1.00033.001/CLBJ/2023-06` endpoint that **phenology images aren't served through NEON's API at all** — `files`/`packages` both come back empty, with an `externalData` entry pointing to the PhenoCam Network's own site: `https://phenocam.nau.edu/webcam/sites/NEON.D11.CLBJ.DP1.00033/`. `neonutilities` cannot pull this product; had to work with PhenoCam Network's own archive URLs directly.

**ROI investigation** — CLBJ has three regions-of-interest, discovered via the site's own webpage (`DB_1000`, `DB_2000`, `DB_3000`) plus real archive URLs following the pattern `https://phenocam.nau.edu/data/archive/{site}/ROI/{site}_{roi}_{1day|3day}.csv`:
- **Lesson (important): the HTTP `Last-Modified` header is misleading for these files** — `DB_1000` and `DB_2000` both showed recent-looking `Last-Modified` timestamps (Jan 2021 and "yesterday" respectively) despite their actual content having stopped years earlier. Had to check the real tail-of-file data rows, not just the header, to find true currency. (Guess: PhenoCam periodically re-touches/regenerates these files even when no new rows get appended.)
- **`DB_1000`**: 2017 → dead 2017-12-07.
- **`DB_2000`**: 2017-12-07 → 2024-01-08 (covers our full 2021-07 start point).
- **`DB_3000`**: 2024-01-24 → present (2026-07-13 as of this session) — the currently-active ROI.
- **~16-day gap** between `DB_2000` ending and `DB_3000` starting (2024-01-09 through 2024-01-23) — real, small, accepted as-is rather than chased down further.
- Real image size confirmed directly (not estimated): **382,951 bytes (~374KB)** per JPEG, sampled from a real `DB_3000` file from 2026-07-13.

**Cadence decision — native (~40 images/day) dropped in favor of once-daily**: the summary CSVs (`1day`/`3day`) only ever reference **one representative "midday" image per period**, not a full manifest of every image captured that day. Confirmed this is the actual sanctioned access pattern, not a gap in our understanding — PhenoCam's own official `phenocamapi` R package's real download function is literally named `download_midday_images()`. Getting every native image (~72,000 over 5 years, ~27GB estimated) would mean either brute-force-guessing timestamps against the raw archive path (unreliable — capture times are irregular, e.g. `115500` vs `121000`, not a fixed schedule) or a direct bulk-access request to PhenoCam Network admins. **Decision**: use the once-daily midday images for now (workshop timeline) — real, supported, ~0.65GB total for the full window. **Explicitly deferred, not forgotten**: if a later model-training effort needs the full native ~40/day resolution, ask PhenoCam Network directly for raw archive access at that point.

**Download script built and run on H037** (`~/pull-phenocam.py`, created via `nano` after a `cat << 'PYEOF'` heredoc paste got corrupted mid-transfer — large multi-line pastes into a live SSH terminal can arrive out of order; `nano` handled the same paste reliably). Stitches `DB_2000`'s `1day.csv` (2021-07-01 → 2024-01-08) and `DB_3000`'s `1day.csv` (2024-01-24 → 2026-06-30), pulls each day's real `midday_filename`, downloads from `.../archive/{site}/{year}/{month}/{filename}`, and writes a manifest CSV (date/roi/filename/GCC values/status) alongside the images. **Result: 1,759 images downloaded, 52 days skipped (no image that day), 0 failures** — exactly matches 922+889=1,811 total days in range. Images and manifest live locally on H037 only (`~/clbj_phenocam_images/`, `~/clbj_phenocam_manifest.csv`) — not yet pushed anywhere else, since the Hugging Face workflow below was set up for the *soil moisture* pipeline first; extending it to these images is a natural next step but wasn't done this session.

### Workshop-wide instruction: acquired data goes to Hugging Face, not just local disk
Learned mid-session that data acquisition for the workshop is expected to go to each participant's Hugging Face account, so it can be shared across the team and used to train a model later — not just sit on local/node disk. Applied this to the **soil moisture** pipeline (the PhenoCam images above are local-only for now, flagged above as a follow-up).

**Setup** (all on the laptop, not H037 — the soil moisture pipeline has always run there):
1. Created a Hugging Face **Write**-scoped access token via `huggingface.co/settings/tokens`, saved to `C:\Users\mlevij\OneDrive - Colostate\Levi\Hugging Face\.huggingface_token`.
2. `py -3.10 -m pip install huggingface_hub` — clean install, no issues.
3. Verified auth via `login()`/`whoami()` before doing anything else — confirmed `repo.write` permission before relying on it.
4. Created a new **private** dataset repo: `mlevij/neon_CLBJ` (named to match a colleague's existing naming convention, not the `clbj-soil-moisture` name first suggested).
5. Wrote `scripts/pipeline/upload_to_hf.py` (new, 6th step in the pipeline) — uploads the daily/weekly/monthly CSVs plus `clbj_data.json`/`clbj_wfp_fc_sat.json` via `HfApi.upload_file()`.

**Verified end to end**: first ran the upload against already-existing (2026-07-22) pipeline output to prove the mechanism, confirmed via `list_repo_files()` that all 5 files landed correctly. Then did a genuine fresh re-run of the whole chain — updated `pull_5yr_swc.py`'s `enddate` from `2026-06` to `2026-07`, re-ran `pull_5yr_swc.py` → `aggregate_swc.py` → `build_json.py` → `upload_to_hf.py`. **Real finding**: the re-upload correctly reported "No files have been modified since last commit" for all 5 files and skipped creating empty commits — NEON hadn't actually published July 2026 data yet (normal processing lag), so the freshly-regenerated output was byte-identical to what was already on Hugging Face. Confirms the upload step is properly idempotent, not just "always commits something."

### Repo cleanup: stale CPER drought-monitor page deleted
User asked to delete the original CPER-era `drought-monitor/index.html` (plus its `data.json`/`wfp_fc_sat.json`) now that `clbj.html`/`clbj_data.json`/`clbj_wfp_fc_sat.json` are the only real, current copies (matches the live site and the new HF-uploaded data). Confirmed via grep no other code referenced the CPER files before deleting (`git rm -f`, since `index.html` still had an uncommitted opacity-tweak diff sitting on it from earlier in the day that's moot once the file's gone). `scripts/README.md`'s "Planned, not yet built" section (daily aggregation + date-range selector) was also stale — both shipped weeks ago — updated to reflect actual current state instead.

---

## Open items / unresolved
- Unidentified FT232 USB-serial device (`/dev/ttyUSB0`) on H02E — GPS suspected, unconfirmed.
- `sage_data_client` assignment part 2 (latest temp, all nodes, last 5 min) — script pattern known, not yet run/confirmed.
- Precip units for `env.raingauge.total_acc` (Hydreon RG-15) — mm strongly assumed from value magnitude, not confirmed from device config or an independent cross-check.
- Whether W021's 54.52°C reading has the same core/shield sensor-placement split diagnosed on W06C — not directly checked.
- Full VS Code Remote-SSH GUI experience on H037 still doesn't work (config-file-scope fix applied but still failed to connect) — fell back to plain terminal-in-VS-Code instead. Not blocking, but unresolved if the full remote-window experience (file browser, etc.) is wanted later.
- PhenoCam raw/native image archive access (~40 images/day instead of once-daily) — deliberately deferred; would need a direct request to PhenoCam Network admins if a future model-training effort needs it.
- The `DB_2000`→`DB_3000` ROI splice has a real ~16-day gap (2024-01-09 through 2024-01-23) with no CLBJ phenocam data at all — accepted as negligible, not investigated further.
- **PhenoCam images not yet pushed to Hugging Face** — 1,759 downloaded images + manifest currently sit local-only on H037 (`~/clbj_phenocam_images/`, `~/clbj_phenocam_manifest.csv`); the HF upload workflow was only built for the soil moisture pipeline so far. Natural next step, not done this session.
- Git push authentication from H02E is unresolved — pushes currently require the GitHub web UI as a workaround.
