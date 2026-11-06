# Optional AI and Image Generation

**You do not need AI to use Campaign Forge's campaign editor, Archives, or PDF tools.** This page separates the currently public features from experimental integrations.

## Writing help: The Oracle

Campaign Forge can use **Ollama** with a separately installed local model for some writing and project-assistance tasks. Depending on the feature, an external API may also be configured explicitly.

- Local models can run on your own computer, subject to the model's hardware requirements.
- Cloud APIs may send selected prompts or content to the provider and may charge your own account.
- AI-written or AI-extracted content can be inaccurate. Review suggestions before accepting them.
- Campaign Forge does not include a model, paid API credits, or a cloud subscription.

See [API and Data Notice](https://github.com/liamupchurch-hue/CampaignForge/blob/main/API_AND_DATA_NOTICE.md) before using an external provider.

## Images: ComfyUI and SDXL

### Public v1.0.0

The public beta offers **guided ComfyUI/SDXL setup** through Cartography, but actual image generation takes place **in ComfyUI**, not directly inside Campaign Forge.

1. Install **ComfyUI Desktop** independently from its official project.
2. Set up and launch a compatible local instance using the appropriate GPU configuration.
3. Install an SDXL Base 1.0 checkpoint into ComfyUI's models/checkpoints directory, or select the shared checkpoint folder already in use.
4. Confirm ComfyUI can load the checkpoint and generate an image.

The optional SDXL Base checkpoint is a **large download (approximately 6.94 GB)**. Check storage space, third-party model terms, and download costs first.

### Experimental Art Studio (v1.1.0 development branch)

The [draft development pull request](https://github.com/liamupchurch-hue/CampaignForge/pull/2) adds a **Generate Image (ComfyUI)** interface under Cartography.

Its intended workflow is:

1. Launch ComfyUI Desktop and a running local instance.
2. Open Campaign Forge's **Generate Image (ComfyUI)** window.
3. Use **Find / Connect** to locate the running local instance.
4. Use **Check Model Status** or the model dropdown to inspect detected model files.
5. Choose an available model and **Low, Medium, or High** quality.
6. Enter a **positive prompt** (what you want) and a **negative prompt** (what to avoid).
7. Click **Generate Image**, then preview and optionally save it to The Archives or as a PNG.

The interface is **experimental**. The model-family integrations may require specific text encoders, diffusion models, and VAE files. A model shown in ComfyUI is not necessarily compatible with every preset. Campaign Forge should stop and explain missing components rather than secretly switching to another model.

## Do updates reinstall AI models?

**No, not by design.** Campaign Forge and ComfyUI are separate applications. Installing a newer Campaign Forge source version does not itself remove ComfyUI's model files.

If Campaign Forge reports SDXL as missing even though ComfyUI can generate with it:

- Check that ComfyUI's instance is running.
- Use **Check Model Status** in the development interface.
- Confirm ComfyUI sees the expected checkpoint filename.
- Check the **shared models/checkpoints** directory or the manually configured model folder.
- Avoid downloading another multi-gigabyte checkpoint until you've checked the existing installation.

## Image quality and model selection

Low, Medium, and High control generation parameters such as image size or sampling steps. **They do not magically upgrade an older model's capabilities.** More advanced models may give better results, but often require more GPU memory, additional model components, and a different workflow.

SDXL is our verified baseline; support for other architectures remains a testing project. No image model weights are distributed with Campaign Forge.

## Privacy and safety

The built-in local ComfyUI workflow is designed for an explicitly connected local service. Models, GPUs, other ComfyUI workflows, and external services are independent third-party software. Check each model's license and never assume generated content or training data is free from rights restrictions.
