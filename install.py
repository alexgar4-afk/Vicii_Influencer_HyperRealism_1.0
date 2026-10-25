#!/usr/bin/env python3
"""Vicii Influencer Hyperrealism installer.

Checks for every custom node pack and model the workflow uses (listed in install_manifest.json)
and installs the missing ones into the right ComfyUI folders. Standard library only, so it runs
on any Python 3.9+; node requirements are installed into ComfyUI's own Python.

    python install.py            # ask the running ComfyUI where its folders are
    python install.py --check    # report only
    python install.py --help     # all options
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "install_manifest.json"
DEFAULT_SERVERS = ("http://127.0.0.1:8188", "http://127.0.0.1:8000")
# ComfyUI's own default subfolders, in its search order (folder_paths.py).
COMFY_SUBFOLDERS = {"diffusion_models": ["unet", "diffusion_models"], "text_encoders": ["text_encoders", "clip"]}
LEGACY = {"unet": "diffusion_models", "clip": "text_encoders"}
USER_AGENT = "Vicii-Influencer-Installer/1.0"
CHUNK = 8 * 1024 * 1024


class DownloadError(Exception):
    pass


# --- model folders: mirrors ComfyUI's folder_paths.add_model_folder_path / load_extra_path_config ---

def add_model_path(paths: dict[str, list[str]], folder: str, path: str, is_default: bool = False) -> None:
    dirs = paths.setdefault(LEGACY.get(folder, folder), [])
    if path in dirs:
        if is_default:
            dirs.remove(path)
            dirs.insert(0, path)
    elif is_default:
        dirs.insert(0, path)
    else:
        dirs.append(path)


def extra_config_entries(config: dict | None, yaml_dir: str) -> list[tuple[str, str, bool]]:
    """(folder, path, is_default) for every path in a parsed extra_model_paths.yaml."""
    entries = []
    for conf in (config or {}).values():
        if not conf:
            continue
        conf = dict(conf)
        base = conf.pop("base_path", None)
        if base:
            base = os.path.expandvars(os.path.expanduser(base))
            if not os.path.isabs(base):
                base = os.path.abspath(os.path.join(yaml_dir, base))
        is_default = bool(conf.pop("is_default", False))
        for folder, value in conf.items():
            for sub in str(value).split("\n"):
                if not sub:
                    continue
                if base:
                    full = os.path.join(base, sub)
                elif os.path.isabs(sub):
                    full = sub
                else:
                    full = os.path.abspath(os.path.join(yaml_dir, sub))
                entries.append((folder, os.path.normpath(full), is_default))
    return entries


def offline_folder_paths(base: Path, folders) -> dict[str, list[str]]:
    paths = {"custom_nodes": [str(base / "custom_nodes")]}
    for folder in folders:
        paths[folder] = [str(base / "models" / sub) for sub in COMFY_SUBFOLDERS.get(folder, [folder])]
    return paths


def target_dir(dirs: list[str], folder: str) -> str:
    """Where a new model goes: the first path named after its folder (so models/diffusion_models, not models/unet)."""
    for d in dirs:
        if os.path.basename(os.path.normpath(d)) == folder:
            return d
    return dirs[0]


def fetch_folder_paths(server: str, timeout: float = 3.0) -> dict | None:
    try:
        with urllib.request.urlopen(server.rstrip("/") + "/internal/folder_paths", timeout=timeout) as resp:
            return json.loads(resp.read())
    except (OSError, ValueError):
        return None


def read_yaml(path: Path, python: Path) -> dict | None:
    """Parse YAML with ComfyUI's Python (it always has PyYAML), keeping this script stdlib-only."""
    code = "import json, sys, yaml; print(json.dumps(yaml.safe_load(open(sys.argv[1], encoding='utf-8'))))"
    try:
        out = subprocess.run([str(python), "-c", code, str(path)], capture_output=True, text=True, check=True)
        return json.loads(out.stdout)
    except (OSError, subprocess.CalledProcessError, ValueError):
        return None


# --- what's installed ----------------------------------------------------------------------------

def find_model(filename: str, dirs: list[str]) -> Path | None:
    for d in dirs:
        p = Path(d) / filename
        if p.is_file():
            return p
    for d in dirs:
        for root, _subdirs, files in os.walk(d):
            if filename in files:
                return Path(root) / filename
    return None


def find_node_pack(custom_nodes: Path, name: str) -> tuple[str, Path | None]:
    """("installed" | "disabled" | "missing", folder). Matches the folder name case-insensitively,
    since ComfyUI Manager / the registry name folders differently (e.g. comfyui-kjnodes)."""
    if not custom_nodes.is_dir():
        return "missing", None
    disabled = None
    for entry in custom_nodes.iterdir():
        if not entry.is_dir():
            continue
        if entry.name.lower() == name.lower():
            return "installed", entry
        if entry.name.lower() == name.lower() + ".disabled":
            disabled = entry
    return ("disabled", disabled) if disabled else ("missing", None)


def resolve_comfy_base(path: Path) -> Path:
    """Accept the portable root (ComfyUI_windows_portable) as well as the ComfyUI folder inside it."""
    if not (path / "custom_nodes").is_dir() and (path / "ComfyUI" / "custom_nodes").is_dir():
        return path / "ComfyUI"
    return path


def find_comfy_python(base: Path) -> Path | None:
    exe = "Scripts/python.exe" if os.name == "nt" else "bin/python"
    for candidate in (base / ".venv" / exe, base / "venv" / exe,
                      base.parent / "python_embeded" / "python.exe", base / "python_embeded" / "python.exe"):
        if candidate.is_file():
            return candidate
    return None


def select_models(models: list[dict], pipelines: list[str] | None) -> list[dict]:
    return [m for m in models if not pipelines or m["pipeline"] in pipelines]


def _existing(path: str) -> str:
    p = Path(path)
    while not p.exists() and p.parent != p:
        p = p.parent
    return str(p)


def disk_shortfalls(needs, drive=lambda d: os.stat(_existing(d)).st_dev,
                    free=lambda d: shutil.disk_usage(_existing(d)).free) -> list[tuple[str, int, int]]:
    """(first dir on that drive, bytes needed, bytes free) for every drive that's too full."""
    totals: dict = {}
    for d, size in needs:
        key = drive(d)
        if key in totals:
            totals[key][1] += size
        else:
            totals[key] = [d, size]
    return [(d, total, free(d)) for d, total in totals.values() if total > free(d)]


# --- downloads -----------------------------------------------------------------------------------

def download(url: str, dest: Path, size: int, urlopen=None, retries: int = 3) -> None:
    """Download to dest + '.part', resuming a previous partial download, then rename into place."""
    urlopen = urlopen or urllib.request.urlopen
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_name(dest.name + ".part")
    for attempt in range(1, retries + 1):
        have = part.stat().st_size if part.exists() else 0
        if have > size:
            part.unlink()
            have = 0
        if have == size:
            break
        try:
            _fetch(url, part, have, size, urlopen)
            break
        except urllib.error.HTTPError as e:
            raise DownloadError(f"{dest.name}: HTTP {e.code} from {url}") from e
        except OSError as e:
            if attempt == retries:
                raise DownloadError(f"{dest.name}: {e} (run the installer again to resume)") from e
            print(f"\n      connection problem ({e}), retrying...")
            time.sleep(2 * attempt)
    got = part.stat().st_size if part.exists() else 0
    if got != size:
        part.unlink(missing_ok=True)
        raise DownloadError(f"{dest.name}: got {got} bytes, expected {size}")
    os.replace(part, dest)


def _fetch(url: str, part: Path, have: int, size: int, urlopen) -> None:
    headers = {"User-Agent": USER_AGENT}
    if have:
        headers["Range"] = f"bytes={have}-"
    with urlopen(urllib.request.Request(url, headers=headers), timeout=60) as resp:
        if have and resp.status != 206:
            have = 0  # server ignored the Range header: start over
        done, started = have, time.monotonic()
        with open(part, "ab" if have else "wb") as f:
            while chunk := resp.read(CHUNK):
                f.write(chunk)
                done += len(chunk)
                rate = (done - have) / max(time.monotonic() - started, 1e-6)
                print(f"\r      {human(done)} / {human(size)}  ({done * 100 // size}%)  {human(rate)}/s   ",
                      end="", flush=True)
    print()


def human(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.1f} {unit}" if unit != "B" else f"{int(n)} B"
        n /= 1024
    return f"{n:.1f} GB"


# --- CLI -----------------------------------------------------------------------------------------

def parse_args(argv):
    ap = argparse.ArgumentParser(description="Install the custom nodes and models the Vicii Influencer workflow needs.")
    ap.add_argument("--comfyui", help="ComfyUI folder (with custom_nodes/ and models/). Default: ask the running ComfyUI.")
    ap.add_argument("--server", help="Running ComfyUI's address. Default: tries " + " and ".join(DEFAULT_SERVERS))
    ap.add_argument("--python", help="ComfyUI's Python, for node requirements. Default: auto-detect.")
    ap.add_argument("--pipeline", action="append", choices=["A", "B"],
                    help="Only get this pipeline's models (repeatable). Default: both.")
    ap.add_argument("--check", action="store_true", help="Only report what's missing; install nothing.")
    ap.add_argument("--yes", action="store_true", help="Don't ask before installing.")
    return ap.parse_args(argv)


def locate_comfyui(args, folders) -> tuple[dict | None, str]:
    """ComfyUI's folder paths, and a description of where they came from."""
    if not args.comfyui:
        for server in [args.server] if args.server else DEFAULT_SERVERS:
            paths = fetch_folder_paths(server)
            if paths and paths.get("custom_nodes"):
                return paths, f"running ComfyUI at {server}"
        print("Can't reach ComfyUI" + (f" at {args.server}" if args.server else " on ports 8188 or 8000") + ".")
        if args.server or not sys.stdin.isatty():
            print("Start ComfyUI and run this again, or pass --comfyui with your ComfyUI folder.")
            return None, ""
        args.comfyui = input("Start ComfyUI and run this again (recommended), or enter your ComfyUI folder: ").strip(' "')
        if not args.comfyui:
            return None, ""

    base = resolve_comfy_base(Path(args.comfyui).expanduser().resolve())
    if not (base / "custom_nodes").is_dir() and not (base / "models").is_dir():
        print(f"{base} doesn't look like a ComfyUI folder (no custom_nodes/ or models/).")
        return None, ""
    paths = offline_folder_paths(base, folders)
    extra = base / "extra_model_paths.yaml"
    if extra.is_file():
        python = Path(args.python) if args.python else find_comfy_python(base) or Path(sys.executable)
        config = read_yaml(extra, python)
        if config is None:
            print(f"WARNING: couldn't read {extra} (needs PyYAML); models listed there won't be found.")
        for folder, path, is_default in extra_config_entries(config, str(base)):
            add_model_path(paths, folder, path, is_default)
    return paths, "--comfyui folder; shared model folders set up by a desktop app aren't read this way"


def confirm(question: str) -> bool:
    try:
        return input(f"{question} [y/N] ").strip().lower() in ("y", "yes")
    except EOFError:
        return False


def run(cmd, **kwargs) -> bool:
    print("      $ " + " ".join(f'"{c}"' if " " in str(c) else str(c) for c in cmd))
    return subprocess.run([str(c) for c in cmd], check=False, **kwargs).returncode == 0


def run_quiet(cmd) -> bool:
    return subprocess.run([str(c) for c in cmd], check=False, capture_output=True).returncode == 0


def main(argv=None) -> int:
    args = parse_args(argv)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    models = select_models(manifest["models"], args.pipeline)
    print(f"Vicii Influencer Hyperrealism installer: {manifest['workflow']}\n")

    paths, source = locate_comfyui(args, sorted({m["folder"] for m in models}))
    if paths is None:
        return 2
    custom_nodes = Path(paths["custom_nodes"][0])
    python = Path(args.python) if args.python else find_comfy_python(custom_nodes.parent)
    print(f"ComfyUI:   {custom_nodes.parent}")
    print(f"Found via: {source}")
    print(f"Python:    {python or 'not found (pass --python to install node requirements)'}\n")

    problems = 0
    print("Custom nodes")
    missing_nodes = []
    for pack in manifest["custom_nodes"]:
        state, folder = find_node_pack(custom_nodes, pack["name"])
        if state == "installed":
            print(f"  OK       {pack['name']:<32} {folder}")
        elif state == "disabled":
            problems += 1
            print(f"  DISABLED {pack['name']:<32} {folder}  -> enable it in ComfyUI Manager, then restart")
        else:
            missing_nodes.append(pack)
            print(f"  MISSING  {pack['name']:<32} -> git clone {pack['repo']}")

    label = " + ".join(sorted({m["pipeline"] for m in models}))
    print(f"\nModels (pipeline {label})")
    missing_models = []
    for m in models:
        dirs = paths.get(m["folder"])
        if not dirs:
            problems += 1
            print(f"  ERROR    [{m['pipeline']}] {m['file']}: ComfyUI has no '{m['folder']}' folder. Update ComfyUI.")
            continue
        found = find_model(m["file"], dirs)
        if found is None:
            dest = Path(target_dir(dirs, m["folder"])) / m["file"]
            missing_models.append((m, dest))
            print(f"  MISSING  [{m['pipeline']}] {m['file']}  {human(m['size'])} -> {dest.parent}")
        elif str(found.parent) in [os.path.normpath(d) for d in dirs]:
            print(f"  OK       [{m['pipeline']}] {m['file']}  {found.parent}")
        else:
            print(f"  OK       [{m['pipeline']}] {m['file']}  {found.parent}  (in a subfolder: re-select it in its loader)")

    uses_b = any(m["pipeline"] == "B" for m in models)
    if uses_b and python is not None and not run_quiet([python, "-c", "import sageattention"]):
        print("\nNote: 'sageattention' isn't installed. In pipeline B, set Patch Sage Attention KJ to disabled.")

    if not missing_nodes and not missing_models:
        if not problems:
            print("\nEverything the workflow needs is installed.")
        return 1 if problems else 0
    total = sum(m["size"] for m, _ in missing_models)
    print(f"\nTo install: {len(missing_nodes)} node pack(s), {len(missing_models)} model(s) ({human(total)}).")
    if args.check:
        return 1

    shortfalls = disk_shortfalls([(str(dest.parent), m["size"]) for m, dest in missing_models])
    for d, needed, free in shortfalls:
        print(f"Not enough disk space for {d}: needs {human(needed)}, {human(free)} free.")
    if shortfalls:
        return 1
    if missing_nodes and not shutil.which("git"):
        print("Git isn't installed (https://git-scm.com/downloads). Install it, or add the node packs with ComfyUI Manager.")
        return 1
    if not args.yes and not confirm("Go ahead?"):
        print("Nothing installed.")
        return 1

    failed, cloned, downloaded = [], 0, 0
    for pack in missing_nodes:
        print(f"\n  Installing {pack['name']}")
        dest = custom_nodes / pack["name"]
        if not run(["git", "clone", "--depth", "1", pack["repo"], dest]):
            failed.append(pack["name"])
            continue
        cloned += 1
        req = dest / "requirements.txt"
        if req.is_file():
            if python is None:
                print(f"      WARNING: install {req} into ComfyUI's Python yourself (pass --python next time).")
            elif not run([python, "-m", "pip", "install", "-r", req]):
                failed.append(f"{pack['name']} requirements")

    for i, (m, dest) in enumerate(missing_models, 1):
        print(f"\n  [{i}/{len(missing_models)}] {m['file']} -> {dest.parent}")
        try:
            download(m["url"], dest, m["size"])
            downloaded += 1
        except DownloadError as e:
            print(f"      FAILED: {e}")
            failed.append(m["file"])

    print()
    if failed:
        print("Failed: " + ", ".join(failed))
    if cloned:
        print("Restart ComfyUI so it loads the new custom nodes.")
    elif downloaded:
        print("Press R on the ComfyUI canvas so the loaders list the new models.")
    if uses_b:
        print("Pipeline B's live preview needs Settings -> preview method -> TAESD.")
    return 1 if failed or problems else 0


if __name__ == "__main__":
    sys.exit(main())
