import io
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

import install

PKG = Path(__file__).resolve().parent.parent
MANIFEST = json.loads((PKG / "install_manifest.json").read_text(encoding="utf-8"))
WORKFLOW = json.loads((PKG / MANIFEST["workflow"]).read_text(encoding="utf-8"))

# Every node type in the workflow that ships with ComfyUI itself. A new type that's neither
# here nor in the manifest fails test_manifest_covers_every_custom_node_type.
CORE_NODE_TYPES = {
    "CLIPLoader", "ComfySwitchNode", "EmptyFlux2LatentImage", "EmptyLatentImage", "ImageCompare",
    "KSampler", "LoadImage", "LoraLoaderModelOnly", "MarkdownNote", "Note", "PreviewAny",
    "PrimitiveString", "PrimitiveStringMultiline", "QwenImage21Cache", "RescaleCFG",
    "ResolutionSelector", "SaveImage", "SkipLayerGuidanceDiTSimple", "StringConcatenate",
    "StringReplace", "TextEncodeQwenImage21", "UNETLoader", "VAEDecode", "VAELoader",
}
MODEL_EXTS = (".safetensors", ".pth", ".pt", ".ckpt", ".bin", ".gguf", ".sft")


# --- manifest stays in sync with the workflow -------------------------------------------

def test_manifest_lists_every_model_file_the_workflow_loads():
    referenced = {
        v for n in WORKFLOW["nodes"] for v in n.get("widgets_values") or []
        if isinstance(v, str) and v.lower().endswith(MODEL_EXTS)
    }
    assert referenced <= {m["file"] for m in MANIFEST["models"]}


def test_manifest_covers_every_custom_node_type():
    workflow_types = {n["type"] for n in WORKFLOW["nodes"]}
    manifest_types = {t for p in MANIFEST["custom_nodes"] for t in p["node_types"]}
    assert workflow_types - CORE_NODE_TYPES == manifest_types


def test_every_manifest_model_has_a_pipeline_size_and_url():
    for m in MANIFEST["models"]:
        assert m["pipeline"] in ("A", "B"), m
        assert m["size"] > 0 and m["url"].startswith("https://"), m


# --- model folders, mirroring ComfyUI's folder_paths ------------------------------------

def test_add_model_path_maps_legacy_names_and_appends():
    paths = {"diffusion_models": ["/m/unet", "/m/diffusion_models"]}
    install.add_model_path(paths, "unet", "/x/unet")
    assert paths["diffusion_models"] == ["/m/unet", "/m/diffusion_models", "/x/unet"]


def test_add_model_path_default_goes_first_and_is_not_duplicated():
    paths = {"loras": ["/m/loras", "/x/loras"]}
    install.add_model_path(paths, "loras", "/x/loras", is_default=True)
    install.add_model_path(paths, "loras", "/y/loras", is_default=True)
    assert paths["loras"] == ["/y/loras", "/x/loras", "/m/loras"]


def test_add_model_path_creates_unknown_folder():
    paths = {}
    install.add_model_path(paths, "vae_approx", "/x/vae_approx")
    assert paths == {"vae_approx": ["/x/vae_approx"]}


def test_extra_config_entries_resolves_base_path_and_multiline(tmp_path):
    shared = tmp_path / "shared"
    config = {
        "shared": {"base_path": str(shared), "is_default": True, "loras": "loras/\nmore_loras/", "vae": "vae/"},
        "empty": None,
        "relative": {"base_path": "../other", "vae": "vae"},
        "no_base": {"text_encoders": "te"},
    }
    entries = install.extra_config_entries(config, str(tmp_path))
    assert entries == [
        ("loras", str(shared / "loras"), True),
        ("loras", str(shared / "more_loras"), True),
        ("vae", str(shared / "vae"), True),
        ("vae", str(tmp_path.parent / "other" / "vae"), False),
        ("text_encoders", str(tmp_path / "te"), False),
    ]


def test_offline_folder_paths_uses_comfyui_defaults(tmp_path):
    paths = install.offline_folder_paths(tmp_path, ["diffusion_models", "text_encoders", "vae_approx"])
    models = tmp_path / "models"
    assert paths == {
        "custom_nodes": [str(tmp_path / "custom_nodes")],
        "diffusion_models": [str(models / "unet"), str(models / "diffusion_models")],
        "text_encoders": [str(models / "text_encoders"), str(models / "clip")],
        "vae_approx": [str(models / "vae_approx")],
    }


def test_target_dir_prefers_first_path_named_after_the_folder():
    assert install.target_dir(["/m/unet", "/m/diffusion_models"], "diffusion_models") == "/m/diffusion_models"
    assert install.target_dir(["/shared/diffusion_models", "/m/unet"], "diffusion_models") == "/shared/diffusion_models"
    assert install.target_dir(["/odd/place"], "loras") == "/odd/place"


# --- finding what's installed -------------------------------------------------------------

def test_find_model_prefers_top_level_then_searches_subfolders(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    (b / "sub").mkdir(parents=True)
    a.mkdir()
    (b / "sub" / "m.safetensors").write_bytes(b"x")
    assert install.find_model("m.safetensors", [str(a), str(b)]) == b / "sub" / "m.safetensors"
    (a / "m.safetensors").write_bytes(b"x")
    assert install.find_model("m.safetensors", [str(b), str(a)]) == a / "m.safetensors"


def test_find_model_ignores_partial_downloads_and_missing_dirs(tmp_path):
    (tmp_path / "m.safetensors.part").write_bytes(b"x")
    assert install.find_model("m.safetensors", [str(tmp_path), str(tmp_path / "nope")]) is None


def test_find_node_pack_matches_folder_case_insensitively(tmp_path):
    (tmp_path / "comfyui-kjnodes").mkdir()
    assert install.find_node_pack(tmp_path, "ComfyUI-KJNodes") == ("installed", tmp_path / "comfyui-kjnodes")


def test_find_node_pack_reports_disabled_and_missing(tmp_path):
    (tmp_path / "rgthree-comfy.disabled").mkdir()
    (tmp_path / "ComfyUI-Spectrum-MOSS.zip").write_bytes(b"")
    assert install.find_node_pack(tmp_path, "rgthree-comfy") == ("disabled", tmp_path / "rgthree-comfy.disabled")
    assert install.find_node_pack(tmp_path, "ComfyUI-Spectrum-MOSS") == ("missing", None)
    assert install.find_node_pack(tmp_path / "nope", "x") == ("missing", None)


def test_resolve_comfy_base_steps_into_portable_folder(tmp_path):
    (tmp_path / "ComfyUI" / "custom_nodes").mkdir(parents=True)
    assert install.resolve_comfy_base(tmp_path) == tmp_path / "ComfyUI"
    assert install.resolve_comfy_base(tmp_path / "ComfyUI") == tmp_path / "ComfyUI"


def test_find_comfy_python_checks_portable_and_venv_layouts(tmp_path):
    base = tmp_path / "ComfyUI"
    base.mkdir()
    assert install.find_comfy_python(base) is None
    embedded = tmp_path / "python_embeded" / "python.exe"
    embedded.parent.mkdir()
    embedded.write_bytes(b"")
    assert install.find_comfy_python(base) == embedded
    venv = base / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    venv.parent.mkdir(parents=True)
    venv.write_bytes(b"")
    assert install.find_comfy_python(base) == venv


def test_select_models_filters_by_pipeline():
    models = [{"file": "a", "pipeline": "A"}, {"file": "b", "pipeline": "B"}]
    assert install.select_models(models, None) == models
    assert install.select_models(models, ["B"]) == [models[1]]


def test_disk_shortfalls_sums_files_per_drive():
    needs = [("/d1/loras", 60), ("/d1/vae", 50), ("/d2/vae", 10)]
    drives = {"/d1/loras": "d1", "/d1/vae": "d1", "/d2/vae": "d2"}
    free = {"d1": 100, "d2": 100}
    short = install.disk_shortfalls(needs, drive=drives.__getitem__, free=lambda d: free[drives[d]])
    assert short == [("/d1/loras", 110, 100)]


# --- downloads ------------------------------------------------------------------------------

class FakeResponse(io.BytesIO):
    def __init__(self, body, status=200, length=None):
        super().__init__(body)
        self.status = status
        self.headers = {"Content-Length": str(len(body) if length is None else length)}

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FakeOpener:
    def __init__(self, data, honor_range=True):
        self.data, self.honor_range, self.requests = data, honor_range, []

    def __call__(self, req, timeout=None):
        self.requests.append(req)
        rng = req.get_header("Range")
        if rng and self.honor_range:
            start = int(rng.split("=")[1].rstrip("-"))
            return FakeResponse(self.data[start:], status=206)
        return FakeResponse(self.data)


def test_download_writes_part_file_then_renames(tmp_path):
    dest = tmp_path / "loras" / "m.safetensors"
    opener = FakeOpener(b"0123456789")
    install.download("https://x/m", dest, 10, urlopen=opener)
    assert dest.read_bytes() == b"0123456789"
    assert not dest.with_name("m.safetensors.part").exists()
    assert opener.requests[0].get_header("Range") is None


def test_download_resumes_from_part_file(tmp_path):
    dest = tmp_path / "m.safetensors"
    dest.with_name("m.safetensors.part").write_bytes(b"0123")
    opener = FakeOpener(b"0123456789")
    install.download("https://x/m", dest, 10, urlopen=opener)
    assert dest.read_bytes() == b"0123456789"
    assert opener.requests[0].get_header("Range") == "bytes=4-"


def test_download_restarts_when_server_ignores_range(tmp_path):
    dest = tmp_path / "m.safetensors"
    dest.with_name("m.safetensors.part").write_bytes(b"XXXX")
    install.download("https://x/m", dest, 10, urlopen=FakeOpener(b"0123456789", honor_range=False))
    assert dest.read_bytes() == b"0123456789"


def test_download_rejects_wrong_size_and_drops_the_part_file(tmp_path):
    dest = tmp_path / "m.safetensors"
    with pytest.raises(install.DownloadError):
        install.download("https://x/m", dest, 11, urlopen=FakeOpener(b"0123456789"))
    assert not dest.exists()
    assert not dest.with_name("m.safetensors.part").exists()


def test_download_skips_request_when_part_file_is_already_complete(tmp_path):
    dest = tmp_path / "m.safetensors"
    dest.with_name("m.safetensors.part").write_bytes(b"0123456789")
    opener = FakeOpener(b"0123456789")
    install.download("https://x/m", dest, 10, urlopen=opener)
    assert dest.read_bytes() == b"0123456789"
    assert opener.requests == []


# --- asking a running ComfyUI ---------------------------------------------------------------

@pytest.fixture
def comfy_server():
    body = json.dumps({"loras": ["/m/loras"], "custom_nodes": ["/base/custom_nodes"]}).encode()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            ok = self.path == "/internal/folder_paths"
            self.send_response(200 if ok else 404)
            self.end_headers()
            if ok:
                self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()


def test_fetch_folder_paths_reads_internal_endpoint(comfy_server):
    assert install.fetch_folder_paths(comfy_server) == {"loras": ["/m/loras"], "custom_nodes": ["/base/custom_nodes"]}


def test_fetch_folder_paths_returns_none_when_unreachable():
    assert install.fetch_folder_paths("http://127.0.0.1:9", timeout=0.5) is None
