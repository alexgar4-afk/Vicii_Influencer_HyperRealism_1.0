# Vicii Influencer Hyperrealism 1.0

Realistic, unedited-looking **iPhone-style photos** in ComfyUI, plus a **pose/expression editor**, all in one workflow with an on/off switch per pipeline.

| Pipeline | What it does | Models |
|---|---|---|
| 🅰️ **A · Kromoss generator** | Makes a new iPhone-style photo from a reference photo (optional, highly recommended) and your text. 50 steps; **Spectrum** makes it about **2.2× faster**. | Kromoss (MOSS-Image finetune) |
| 🅱️ **B · Pose + expression edit** | Changes the pose and facial expression of an existing photo. Can also swap in a different face. | Qwen Image 2.1 + BFS head-swap LoRA |

## 📦 What's in the package

| File | What it is |
|---|---|
| `Vicii_Influencer_Hyperrealism_1.0.json` | The ComfyUI workflow (pipelines A and B). Drag it onto the ComfyUI canvas. |
| `install.bat` / `install.py` | Installer: checks for every custom node and model the workflow uses and installs the missing ones. |
| `install_manifest.json` | The list of node packs and models the installer checks (with download links and sizes). |
| `Workflow_Guide.html` | Visual guide to the whole workflow with example images. Open it in any browser; keep it next to `Example Images/`. |
| `Example Images/` | Example outputs made with this workflow (used by the guide). |
| `README.md` | This file. |

Inside the workflow, notes explain everything: **📖 START HERE**, **⬇️ DOWNLOADS**, one note per prompt style, and how-to notes in pipeline B.

## ✅ Requirements

- **ComfyUI 0.42.1 or newer**, with native **MOSS-Image** and **Qwen Image 2.1** support. If `TextEncodeQwenImage21` or `QwenImage21Cache` shows up as a missing node, update ComfyUI.
- An NVIDIA GPU. Tested on an RTX 3090 (24 GB).
- About **29 GB** of disk space for the models: ~11 GB for A and ~18 GB for B.
- **Git** and **Python 3.9+** for the installer.

## 🛠️ Install

### ⚡ Automatic (recommended)

1. **Start ComfyUI** and leave it running. The installer asks it where your model folders are, so it also finds models in shared or extra model folders.
2. Double-click **`install.bat`** (Windows), or run:

   ```bash
   python install.py
   ```

3. It lists what's already installed and what's missing, asks before downloading, then installs:
   - missing **custom nodes** → `git clone` into `custom_nodes/` + their `requirements.txt` into ComfyUI's Python
   - missing **models** → downloaded into ComfyUI's model folders (downloads resume if interrupted; just run it again)
4. **Restart ComfyUI** if it installed custom nodes, or press **R** on the canvas to refresh the model lists.

Useful options:

| Option | What it does |
|---|---|
| `--check` | Only report what's missing. Installs nothing. |
| `--pipeline A` / `--pipeline B` | Only get the models for one pipeline (A ≈ 11 GB, B ≈ 18 GB). Custom nodes are always installed: the workflow needs all of them to load. |
| `--comfyui "C:\path\to\ComfyUI"` | Use this ComfyUI folder (the one with `custom_nodes/` and `models/`) instead of asking the running server. Reads its `extra_model_paths.yaml`, but not a desktop app's shared model folders. |
| `--server http://127.0.0.1:8188` | Address of your running ComfyUI. By default the installer tries ports 8188 and 8000. |
| `--python PATH` | ComfyUI's Python, used to install node requirements. Found automatically for portable, desktop and venv installs. |
| `--yes` | Don't ask before downloading. |

### 🔧 Manual

#### 1. Custom nodes (4)

| Node pack | Used for | Link |
|---|---|---|
| **ComfyUI-Spectrum-MOSS** | A speed-up | https://github.com/Rkkss/ComfyUI-Spectrum-MOSS |
| **ComfyUI-MOSSImageTextEncoder** | A Vision Encode (reference image) | https://github.com/ThetaCursed/ComfyUI-MOSSImageTextEncoder |
| **ComfyUI-KJNodes** | Live preview (A, B) and Sage Attention patch (B) | https://github.com/kijai/ComfyUI-KJNodes |
| **rgthree-comfy** | The 🎛️ PIPELINE TOGGLES panel | https://github.com/rgthree/rgthree-comfy |

Install them with *ComfyUI Manager → Install via Git URL*, or `git clone` them into `ComfyUI/custom_nodes/`, then **restart ComfyUI**. Every other node is built into ComfyUI.

**Patch Sage Attention KJ** (Pipeline B) needs the `sageattention` Python package. If you don't have it, set the node's `sage_attention` to **disabled**.

#### 2. Models

**Pipeline A**

| # | Model | Size | Put it in | Download |
|---|---|---|---|---|
| 1 | Kromoss UNET (INT8) | 5.4 GB | `models/diffusion_models/` | [kromoss_int8_convrot.safetensors](https://huggingface.co/lodestones/Kromoss/resolve/main/diffusion_models/kromoss_int8_convrot.safetensors) |
| 2 | Text encoder (Qwen3.5-9B W4A8) | 5.4 GB | `models/text_encoders/` | [qwen3.5_9b_moss_image_sft_w4a8_gptq.safetensors](https://huggingface.co/nif0/MOSS-Image-SFT-ComfyUI/resolve/main/text_encoders/qwen3.5_9b_moss_image_sft_w4a8_gptq.safetensors) |
| 3 | VAE | 125 MB | `models/vae/` | [moss_image_vae_bf16.safetensors](https://huggingface.co/nif0/MOSS-Image-SFT-ComfyUI/resolve/main/vae/moss_image_vae_bf16.safetensors) |
| 4 | Live-preview decoder (FLUX.2 TAE) | 3.3 MB | `models/vae_approx/` | [TAE_Flux2_AcademiaSD.safetensors](https://huggingface.co/AcademiaSD/TAE_Flux2_AcademiaSD/resolve/main/TAE_Flux2_AcademiaSD.safetensors) |

**Pipeline B**

| # | Model | Size | Put it in | Download |
|---|---|---|---|---|
| 5 | Qwen Image 2.1 (INT8) | 7.3 GB | `models/diffusion_models/` | [qwen_image_2.1_int8_convrot.safetensors](https://huggingface.co/Comfy-Org/Qwen-Image-2.1/resolve/main/diffusion_models/qwen_image_2.1_int8_convrot.safetensors) |
| 6 | Text encoder (Qwen3-VL 8B INT8) | 9.4 GB | `models/text_encoders/` | [qwen3vl_8b_int8_convrot.safetensors](https://huggingface.co/Comfy-Org/Qwen-Image-2.1/resolve/main/text_encoders/qwen3vl_8b_int8_convrot.safetensors) |
| 7 | VAE | 676 MB | `models/vae/` | [qwen_image_2.1_vae_bf16.safetensors](https://huggingface.co/Comfy-Org/Qwen-Image-2.1/resolve/main/vae/qwen_image_2.1_vae_bf16.safetensors) |
| 8 | BFS head-swap LoRA v1.1 | 260 MB | `models/loras/` | [bfs_head_v1.1_qwen_2.1.safetensors](https://huggingface.co/Alissonerdx/BFS-Best-Face-Swap/resolve/main/bfs_head_v1.1_qwen_2.1.safetensors) |
| 9 | 8-step speed LoRA | 336 MB | `models/loras/` | [p_qwen_image_2.1_8step_v0.1-comfyui-T8.safetensors](https://huggingface.co/RunningHubAI/rh-p-qwen-image-2.1-8step-v0.1-comfyui-t8-lora/resolve/main/p_qwen_image_2.1_8step_v0.1-comfyui-T8.safetensors). Rename it to `p_qwen_image_2.1_8step_v0.1.safetensors` (the installer does this for you), or re-select it in the **LoRA · 8-step** loader. |
| 10 | Live-preview decoder (Qwen 2.1 TAE) | 15 MB | `models/vae_approx/` | [taeqi2_1_decoder.pth](https://github.com/madebyollin/taesd/raw/main/taeqi2_1_decoder.pth). Keep this exact file name: ComfyUI looks for it by name. |

### ▶️ Load and run

1. Restart ComfyUI and drag `Vicii_Influencer_Hyperrealism_1.0.json` onto the canvas.
2. If a loader shows red, click it and select the file you downloaded.
3. Set the **🎛️ PIPELINE TOGGLES** panel (top-left) for what you want to do (see below), then press **Run** (Ctrl+Enter).

## 🎛️ Pipeline toggles

The **🎛️ PIPELINE TOGGLES** panel at the top-left has one switch per pipeline. **Off** bypasses every node in that pipeline. The arrow next to each switch jumps to that pipeline on the canvas.

| I want to… | A | B |
|---|---|---|
| Generate a new photo | ✅ | ⬜ |
| Change the pose / expression (or swap a face) | ⬜ | ✅ |

- A switch turns **every** node in its pipeline on or off. If you bypassed a single node by hand (for example Spectrum, with Ctrl+B), switching the pipeline back on re-enables it.

## 🅰️ Pipeline A · Generate

1. Flip the **🎛️ STYLE** switch in group **③ YOUR PROMPT**: ON = 📱 Modern iPhone, OFF = 📼 Cheap phone.
2. Set the **🖼️ REFERENCE** switch and load a photo into **🖼️ REFERENCE IMAGE** (see below). The reference is optional but highly recommended.
3. Write your prompt in the big **✏️** box. The 🔧 Prompt Builder adds the opener, beauty clause and closing block for you.
4. Pick a size in **Resolution Selector** and run. Images save to `output/kromoss/`.

The Prompt Builder follows this formula:

```
[OPENER + BEAUTY CLAUSE] + [your subject & scene] + [CLOSING BLOCK]
```

| Style | Opener + beauty clause | Look |
|---|---|---|
| 📱 **Modern iPhone** | `modern sharp iPhone 16 Pro main camera photo of a 22-year-old very attractive influencer girl with a slim hourglass shape` | Crisp, HDR, clean. For daylight, travel and lifestyle shots. |
| 📼 **Cheap phone** | `Cheap phone iPhone grainy amateur of a 22-year-old very attractive influencer girl with full lips, long eyelashes and a slim hourglass shape,` | Heavy grain and motion softness. For night, indoor and candid shots. The **🏷️ Scene word** fills `[SCENE]` in its closing block. |

The full closing blocks and examples are in the two style notes inside the workflow.

### 🖼️ Reference image: optional, highly recommended

| Switch | What happens | What you write in the ✏️ box |
|---|---|---|
| ✅ **ON** (recommended) | Qwen3.5's vision tower reads the photo and encodes its elements (outfit, hair, jewelry, light, setting, vibe) **straight into the conditioning**. You don't need an LLM to extract a prompt from the photo first. | Only what should change: pose, clothes, expression. Example: `wearing a camo cap, doing the middle finger` |
| ⬜ **OFF** | Text only: nothing comes from a photo. | A **full, detailed prompt**, starting with her hair: face, body, outfit, pose, setting, lighting, framing. |

The reference is strong: in testing, a bedroom-selfie reference carried its outfit, hair color, jewelry and even background props past a beach prompt. Crop it tight on the person if you only want the look. `image_weight` 0.25–0.5 only softens it a little.

### 📸 Pipeline A in action

![Pipeline A on the ComfyUI canvas: the prompt box, the reference photo, the Prompt Builder, the KSampler, the saved 1088 × 1920 image and the live preview](Example%20Images/Screenshots/pipeline-a-canvas.webp)

A run with a reference photo: the ✏️ box holds only `wearing a camo cap , doing the middle finger`, the 🖼️ REFERENCE switch is on with a ramen-restaurant photo, and STYLE is on (📱 Modern). The 🔧 Prompt Builder (top right) wraps the text in the opener and closing block, the KSampler runs 50 steps at CFG 3, and Save Image shows the 1088 × 1920 result next to the 👁️ live preview.

## 👁️ Live preview: spot a bad run early and cancel it

<img src="Example%20Images/Screenshots/live-preview.png" width="320" alt="Model Preview Override at step 5 of 50: still blurry, but the pose, framing, cap and setting are already readable">

Every pipeline has a **👁️ LIVE PREVIEW** group with **Model Preview Override** (KJNodes). It shows the image *while* it's being generated, not only at the end.

**Why it matters:** you don't have to wait for a render you're going to throw away. In the screenshot the run is at step 5 of 50, about 10 seconds into sampling, and the node estimates ~96 s to go. The picture is still a blur, but the pose, the framing, the cap and the setting already read. If something's off (wrong pose, bad crop, a prop leaking in from the reference), press **✕** next to **Run** to cancel, fix the prompt or seed, and go again. Over a session of tries that's a lot of waiting saved. By about 30% of the steps the face is readable too.

The strip under the preview shows the step, the seconds per step and the time left, plus the noise curve and the time each step took.

- **A** decodes the preview with `TAE_Flux2_AcademiaSD.safetensors`, set in the node's `tiny_vae`.
- **B** keeps `tiny_vae` on **none** on purpose. ComfyUI's own previewer loads `taeqi2_1_decoder.pth` from `models/vae_approx/`; KJ's `tiny_vae` slot can't load that file. This needs ComfyUI's live preview method set to **TAESD** (Settings → search "preview method"). Otherwise B's preview shows blurry color blobs.

## 🅱️ Pipeline B · Change pose + expression

1. **Image 1 · base photo:** the photo to edit. Its body, scene, lighting and outfit carry over.
2. **Image 2 · face / head source:** whose face ends up in the result.
   - The **same photo** as Image 1 means she keeps her own face and only the pose and expression change.
   - A **different person** means a face swap.
3. Edit the prompt in **Prompt · BFS head swap + new pose / expression** and run. Images save to `output/qwen-2.1/bfs-pose-expr_*.png`.

**Prompt rules.** The BFS LoRA was trained on a single caption. The first part of the prompt is that caption, word for word. **Don't change it:**

```
head_swap: start with <image1> as the base image, keeping its lighting, environment, and background, … remove the head from <image1> completely and replace it with the head from <image2>, strictly preserving the hair, eye color, nose structure from <image2>.
```

Edit only the two sentences after it:

- `change the facial expression: …` (for example: laughing hard, eyes squeezed almost shut, cheeks pushed up)
- `change the pose: …` (say which hand moves where; keep the face turned toward the camera)

Tips:

- **Keep hands off the eyes and nose.** A hand over the mouth or chin works. Hands across the eyes or nose are where the face swap breaks.
- BFS normally *copies* the expression from Image 1. The prompt overrides that, but if the old expression bleeds through, try another seed.
- **Size switch:** OFF (default) matches Image 1's size, which keeps the head in the same place. ON uses the Resolution Selector.
- **Image 3** is unwired on purpose: BFS is a 2-image LoRA, and the pipeline switch would otherwise turn it back on.
- B's output is a little softer than the source photo.

### 📸 Pipeline B in action: a head swap

![Pipeline B on the ComfyUI canvas: models, Image 1 base photo, Image 2 face, the head-swap prompt, size, sampler, the saved result, the compare slider and the live preview](Example%20Images/Screenshots/pipeline-b-canvas.webp)

Left to right: the **Models** group (Qwen Image 2.1 INT8, the Qwen3-VL text encoder, the BFS head LoRA at 0.9 and the 8-step LoRA), then **Image 1** (the photo to keep: pose, outfit, car, street), **Image 2** (the new face) and **Image 3** (bypassed). Then the **Prompt** with the BFS caption, **Size** (switch off, so the result matches Image 1 at 1088 × 1920), the **Sampler** (20 steps, CFG 3, seed 43), the saved result, **🔍 Compare** (drag to flip between Image 1 and the swap) and **👁️ B's live preview**.

## ⚙️ Settings: what to touch and what not to

| | ✅ Safe to change | 🛑 Leave alone |
|---|---|---|
| **A** | Subject & scene text, STYLE switch, Scene word, reference image, Resolution Selector, seed, sampler (`dpmpp_2m_sde` default, `er_sde`, `sa_solver`) | Steps: keep **50** (Spectrum needs them). Negative prompt: keep it **empty**. Don't add **ModelSamplingSD3**. Don't use `res_multistep_ancestral`. |
| **B** | The `change the facial expression` / `change the pose` sentences, negative prompt, seed, size switch, BFS LoRA strength (the workflow uses 0.9; the model card suggests starting at 1.0) | The `head_swap: …` caption part. The image order: Image 1 = base, Image 2 = face. |

## 🩹 Troubleshooting

- **B's live preview is blurry color blobs:** `taeqi2_1_decoder.pth` is missing from `models/vae_approx/` (the server log says *"could not find models/vae_approx/taeqi2_1_decoder"*), or the live preview method isn't TAESD.
- **"Node type not found: Fast Groups Bypasser (rgthree)":** install rgthree-comfy and restart.
- **"Node type not found: SpectrumMOSSImageManual" (or another custom node):** that custom node isn't installed, or ComfyUI wasn't restarted after installing it. Run `python install.py --check`.
- **A node you bypassed by hand is active again:** the pipeline switch re-enabled it. Bypass it again.
- **Red loader / "value not in list":** re-select the model file in that loader. File names must match what you downloaded.
- **Errors loading the MOSS or Qwen 2.1 models:** your ComfyUI is too old. Update it.
- **Images look broken, burned or neon (A):** check that nothing was added between the loaders and the KSampler (especially ModelSamplingSD3) and that the sampler isn't `res_multistep_ancestral`.
- **Installer: "can't reach ComfyUI":** start ComfyUI first, or pass `--comfyui` with your ComfyUI folder.

## 📄 Licenses

This package contains only the workflow, the installer and documentation. No model weights or third-party code are included; the installer downloads those from their original sources:

- Kromoss: [lodestones/Kromoss](https://huggingface.co/lodestones/Kromoss) (Apache-2.0)
- MOSS text encoder + VAE: [nif0/MOSS-Image-SFT-ComfyUI](https://huggingface.co/nif0/MOSS-Image-SFT-ComfyUI) (Apache-2.0)
- Qwen Image 2.1 model, text encoder + VAE: [Comfy-Org/Qwen-Image-2.1](https://huggingface.co/Comfy-Org/Qwen-Image-2.1) (custom license; see the repo)
- BFS head-swap LoRA: [Alissonerdx/BFS-Best-Face-Swap](https://huggingface.co/Alissonerdx/BFS-Best-Face-Swap) (MIT)
- 8-step speed LoRA: [RunningHubAI/rh-p-qwen-image-2.1-8step-v0.1-comfyui-t8-lora](https://huggingface.co/RunningHubAI/rh-p-qwen-image-2.1-8step-v0.1-comfyui-t8-lora) (no license listed)
- Live-preview decoders: [madebyollin/taesd](https://github.com/madebyollin/taesd) (MIT), [AcademiaSD/TAE_Flux2_AcademiaSD](https://huggingface.co/AcademiaSD/TAE_Flux2_AcademiaSD) (Apache-2.0)
- ComfyUI-Spectrum-MOSS: [Rkkss/ComfyUI-Spectrum-MOSS](https://github.com/Rkkss/ComfyUI-Spectrum-MOSS) (GPL-3.0)
- ComfyUI-MOSSImageTextEncoder: [ThetaCursed/ComfyUI-MOSSImageTextEncoder](https://github.com/ThetaCursed/ComfyUI-MOSSImageTextEncoder) (MIT)
- ComfyUI-KJNodes: [kijai/ComfyUI-KJNodes](https://github.com/kijai/ComfyUI-KJNodes) (GPL-3.0)
- rgthree-comfy: [rgthree/rgthree-comfy](https://github.com/rgthree/rgthree-comfy) (MIT)

**Face swaps:** only swap faces of people who have given consent, and never of public figures.
