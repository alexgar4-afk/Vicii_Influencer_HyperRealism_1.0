# Vicii Influencer Hyperrealism 1.0

A ComfyUI workflow for realistic, unedited-looking **iPhone-style photos**, with two pipelines you switch on and off:

- 🅰️ **A · Generate:** a new iPhone-style photo from your text and an optional reference photo (Kromoss, a MOSS-Image finetune).
- 🅱️ **B · Edit:** a new pose and expression on an existing photo, or a face swap (Qwen Image 2.1 + BFS head-swap LoRA).

For the full visual guide, open `Workflow_Guide.html` in a browser.

## ⚡ Install

**Needs:** ComfyUI 0.42.1+, an NVIDIA GPU (tested on an RTX 3090, 24 GB), ~29 GB of disk, Git and Python 3.9+.

1. **Start ComfyUI.**
2. **Double-click `install.bat`** (or run `python install.py`). It checks the 4 custom node packs and 10 models, lists what's missing, and installs it into the right folders after you confirm.
3. **Restart ComfyUI** and drag `Vicii_Influencer_Hyperrealism_1.0.json` onto the canvas.

```bash
python install.py --check                          # only report what's missing
python install.py --pipeline A                     # only A's models (~11 GB; B is ~18 GB)
python install.py --comfyui "C:\path\to\ComfyUI"   # if ComfyUI isn't running
```

`python install.py --help` lists every option. Interrupted downloads resume when you run it again.

<details>
<summary><b>Manual install (links)</b></summary>

**Custom nodes:** clone into `ComfyUI/custom_nodes/`, then restart ComfyUI.

- [ComfyUI-Spectrum-MOSS](https://github.com/Rkkss/ComfyUI-Spectrum-MOSS): A speed-up
- [ComfyUI-MOSSImageTextEncoder](https://github.com/ThetaCursed/ComfyUI-MOSSImageTextEncoder): A reference photo
- [ComfyUI-KJNodes](https://github.com/kijai/ComfyUI-KJNodes): live preview, B's Sage Attention patch (needs the `sageattention` package; otherwise set the node to disabled)
- [rgthree-comfy](https://github.com/rgthree/rgthree-comfy): the pipeline toggles

**Models**

| Model | Folder | Pipeline |
|---|---|---|
| [kromoss_int8_convrot.safetensors](https://huggingface.co/lodestones/Kromoss/resolve/main/diffusion_models/kromoss_int8_convrot.safetensors) (5.4 GB) | `models/diffusion_models/` | A |
| [qwen3.5_9b_moss_image_sft_w4a8_gptq.safetensors](https://huggingface.co/nif0/MOSS-Image-SFT-ComfyUI/resolve/main/text_encoders/qwen3.5_9b_moss_image_sft_w4a8_gptq.safetensors) (5.4 GB) | `models/text_encoders/` | A |
| [moss_image_vae_bf16.safetensors](https://huggingface.co/nif0/MOSS-Image-SFT-ComfyUI/resolve/main/vae/moss_image_vae_bf16.safetensors) (125 MB) | `models/vae/` | A |
| [TAE_Flux2_AcademiaSD.safetensors](https://huggingface.co/AcademiaSD/TAE_Flux2_AcademiaSD/resolve/main/TAE_Flux2_AcademiaSD.safetensors) (3 MB) | `models/vae_approx/` | A |
| [qwen_image_2.1_int8_convrot.safetensors](https://huggingface.co/Comfy-Org/Qwen-Image-2.1/resolve/main/diffusion_models/qwen_image_2.1_int8_convrot.safetensors) (7.3 GB) | `models/diffusion_models/` | B |
| [qwen3vl_8b_int8_convrot.safetensors](https://huggingface.co/Comfy-Org/Qwen-Image-2.1/resolve/main/text_encoders/qwen3vl_8b_int8_convrot.safetensors) (9.4 GB) | `models/text_encoders/` | B |
| [qwen_image_2.1_vae_bf16.safetensors](https://huggingface.co/Comfy-Org/Qwen-Image-2.1/resolve/main/vae/qwen_image_2.1_vae_bf16.safetensors) (676 MB) | `models/vae/` | B |
| [bfs_head_v1.1_qwen_2.1.safetensors](https://huggingface.co/Alissonerdx/BFS-Best-Face-Swap/resolve/main/bfs_head_v1.1_qwen_2.1.safetensors) (260 MB) | `models/loras/` | B |
| [8-step LoRA](https://huggingface.co/RunningHubAI/rh-p-qwen-image-2.1-8step-v0.1-comfyui-t8-lora/resolve/main/p_qwen_image_2.1_8step_v0.1-comfyui-T8.safetensors) (336 MB): rename to `p_qwen_image_2.1_8step_v0.1.safetensors` | `models/loras/` | B |
| [taeqi2_1_decoder.pth](https://github.com/madebyollin/taesd/raw/main/taeqi2_1_decoder.pth) (15 MB): keep this exact name | `models/vae_approx/` | B |

</details>

## 🎛️ Pick a pipeline

The **🎛️ PIPELINE TOGGLES** panel (top-left) turns each pipeline on or off.

| I want to… | A | B |
|---|---|---|
| Generate a new photo | ✅ | ⬜ |
| Change the pose / expression, or swap a face | ⬜ | ✅ |

## 🅰️ Pipeline A · Generate a photo

1. **STYLE** switch: ON = 📱 Modern iPhone, OFF = 📼 Cheap phone.
2. **REFERENCE** switch ON and load a photo into **🖼️ REFERENCE IMAGE** (optional, highly recommended).
3. **✏️ box:** with a reference, write only what should change. Without one, write a full description, starting with her hair.
4. Pick a size in **Resolution Selector** and press **Run**. Images save to `output/kromoss/`.

The 🔧 Prompt Builder adds the style's opener and closing block around your text, so you only write the middle.

**Result: same prompt, same seed, only STYLE flipped**

| 📱 Modern (ON): crisp, Smart HDR | 📼 Cheap phone (OFF): heavy grain, motion softness |
|:---:|:---:|
| <img src="Example%20Images/style%20comparison/auto_modern_00001_.png" width="300" alt="Modern iPhone style: crisp, clean HDR beach photo"> | <img src="Example%20Images/style%20comparison/auto_cheap_00001_.png" width="300" alt="Cheap phone style: grainy, softer version of the same beach photo"> |

### 🖼️ Reference photo → new photo

**How:** 🖼️ Vision Encode passes the photo through Qwen3.5-9B's vision tower and puts it in the prompt, right before your text. Kromoss then draws a brand-new photo: no pixels are copied.

**Before → after.** Reference ON, and the only text: `wearing a camo cap , doing the middle finger`

| Reference photo | Pipeline A output |
|:---:|:---:|
| <img src="Example%20Images/ref-image-encoding/original_image.png" width="300" alt="Reference photo: a woman in a gray cap and black puffer jacket eating ramen under yellow lanterns and red neon at night"> | <img src="Example%20Images/ref-image-encoding/moss_generation.png" width="300" alt="Pipeline A output: a similar woman in a camo cap at a ramen restaurant, pouting and giving the middle finger"> |

- **Kept from the reference:** the ramen restaurant, lanterns and neon, the bowl and chopsticks, the puffer jacket, the heart necklace, the pout.
- **Changed by the text:** a camo cap and the middle finger.
- **Redrawn:** the face (similar, not the same person), the light (night became day) and the 9:16 framing.

Tips: the reference is strong, so crop it tight on the person if you don't want the room. `image_weight` barely softens it; use the switch to turn it off.

### 📸 On the canvas

<img src="Example%20Images/Screenshots/pipeline-a-canvas.webp" alt="Pipeline A on the ComfyUI canvas: the prompt box, the reference photo, the Prompt Builder, the KSampler, the saved image and the live preview">

### 👁️ Live preview: cancel bad runs early

<img src="Example%20Images/Screenshots/live-preview.png" width="280" alt="Model Preview Override at step 5 of 50: still blurry, but the pose, framing, cap and setting are already readable">

Each pipeline's **👁️ LIVE PREVIEW** shows the image while it renders. At step 5 of 50 (about 10 s in) the pose, framing and setting are already readable. If it's wrong, press **✕** next to **Run**: here that saves the ~96 s still to go.

B's preview needs ComfyUI's preview method set to **TAESD** (Settings → "preview method").

## 🅱️ Pipeline B · New pose + expression

1. **Image 1:** the photo to edit (body, scene, outfit carry over).
2. **Image 2:** the face to use. The same photo keeps her face; a different person makes a face swap.
3. **Prompt:** keep the `head_swap: …` caption as is (the LoRA was trained on it). Edit only the `change the facial expression: …` and `change the pose: …` sentences after it.
4. Press **Run**. Images save to `output/qwen-2.1/`.

**Before → after.** Image 1 and Image 2 are the same photo; the prompt asks for a laugh with her hand over her mouth.

| Before (Pipeline A output) | After (Pipeline B) |
|:---:|:---:|
| <img src="Example%20Images/Carrousel-generator/01_moss_original_.png" width="300" alt="Pipeline A output: woman in a camo cap at a ramen restaurant, pouting, hand raised"> | <img src="Example%20Images/Carrousel-generator/01_qwen_edit_.png" width="300" alt="Pipeline B output: same woman and scene, now laughing with her hand over her mouth"> |

Same face, outfit and scene: a new carousel slide from one shot.

### 🔄 Face swap

Same steps, with a **different person in Image 2**. The body, outfit, pose and scene stay; the face and hair come from Image 2.

| Image 1 · base | Image 2 · face | Result |
|:---:|:---:|:---:|
| <img src="Example%20Images/Face-swap/original_moss_image.png" width="220" alt="Base image: woman in a camo cap at a ramen restaurant"> | <img src="Example%20Images/Face-swap/face_reference.png" width="220" alt="Face reference: AI character with green-and-black hair and a septum ring"> | <img src="Example%20Images/Face-swap/face_swapped_result.png" width="220" alt="Result: the character's face and hair on the ramen-restaurant photo, same pose, cap and outfit"> |

Tips: keep hands off the eyes and nose. Name hats or glasses in the prompt's keep list. Delete from the negative prompt anything the positive asks for.

### 📸 On the canvas

<img src="Example%20Images/Screenshots/pipeline-b-canvas.webp" alt="Pipeline B on the ComfyUI canvas: models, Image 1 base photo, Image 2 face, the head-swap prompt, size, sampler, the saved result, the compare slider and the live preview">

## 🛑 Leave alone

- **A:** keep 50 steps (Spectrum needs them) and an empty negative prompt. Don't add ModelSamplingSD3. Don't use `res_multistep_ancestral`.
- **B:** keep the `head_swap: …` caption and the image order (Image 1 = base, Image 2 = face).

## 🩹 Troubleshooting

| You see | Fix |
|---|---|
| Missing node type | Run `python install.py --check`, then restart ComfyUI. |
| Red loader / "value not in list" | Re-select the model file in that loader. |
| B's live preview is blurry blobs | Get `taeqi2_1_decoder.pth` into `models/vae_approx/` and set the preview method to TAESD. |
| Burned or neon images (A) | Remove any ModelSamplingSD3 node; don't use `res_multistep_ancestral`. |
| Errors loading MOSS or Qwen 2.1 | Update ComfyUI. |
| A node you bypassed is on again | The pipeline switch re-enabled it. Bypass it again. |

## 📄 Licenses

This repo holds only the workflow, the installer and docs; models and node packs download from their sources. Kromoss ([lodestones/Kromoss](https://huggingface.co/lodestones/Kromoss)) and the MOSS text encoder + VAE ([nif0/MOSS-Image-SFT-ComfyUI](https://huggingface.co/nif0/MOSS-Image-SFT-ComfyUI)) are Apache-2.0. Qwen Image 2.1 ([Comfy-Org/Qwen-Image-2.1](https://huggingface.co/Comfy-Org/Qwen-Image-2.1)) has a custom license. The BFS LoRA ([Alissonerdx/BFS-Best-Face-Swap](https://huggingface.co/Alissonerdx/BFS-Best-Face-Swap)) is MIT, and the 8-step LoRA ([RunningHubAI](https://huggingface.co/RunningHubAI/rh-p-qwen-image-2.1-8step-v0.1-comfyui-t8-lora)) lists no license. The preview decoders are MIT ([madebyollin/taesd](https://github.com/madebyollin/taesd)) and Apache-2.0 ([AcademiaSD/TAE_Flux2_AcademiaSD](https://huggingface.co/AcademiaSD/TAE_Flux2_AcademiaSD)). Node packs: Spectrum-MOSS (GPL-3.0), MOSSImageTextEncoder (MIT), KJNodes (GPL-3.0), rgthree-comfy (MIT).

**Face swaps:** only swap faces of people who have given consent, and never of public figures.
