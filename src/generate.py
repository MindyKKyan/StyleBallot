"""Stable Diffusion 1.5 variant generation — local GPU/MPS or HF ZeroGPU."""

from __future__ import annotations

from typing import Callable

import torch
from PIL import Image

from .config import (
    GUIDANCE_SCALE,
    IMAGE_SIZE,
    IS_HF_SPACE,
    NUM_INFERENCE_STEPS,
    NUM_VARIANTS,
    SD_MODEL_ID,
    VARIANT_SEEDS,
)
from .refine import REFINE_SEEDS

_pipe = None


def _maybe_gpu_decorator(fn: Callable) -> Callable:
    if not IS_HF_SPACE:
        return fn
    try:
        import spaces

        return spaces.GPU(duration=120)(fn)
    except ImportError:
        return fn


def _resolve_device() -> tuple[str, torch.dtype]:
    """Pick runtime device from actual availability, not SPACE_ID alone."""
    if torch.cuda.is_available():
        return "cuda", torch.float16
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return "mps", torch.float32
    return "cpu", torch.float32


def _load_pipeline():
    global _pipe
    if _pipe is not None:
        return _pipe

    device_name, dtype = _resolve_device()

    from diffusers import StableDiffusionPipeline

    _pipe = StableDiffusionPipeline.from_pretrained(
        SD_MODEL_ID,
        torch_dtype=dtype,
        safety_checker=None,
        requires_safety_checker=False,
    )
    _pipe = _pipe.to(device_name)
    _pipe.set_progress_bar_config(disable=True)
    return _pipe


def _warmup_pipeline():
    return _load_pipeline()


def _generate_impl(prompt: str, seeds: tuple[int, ...]) -> list[Image.Image]:
    pipe = _warmup_pipeline()
    device_name, _ = _resolve_device()
    images: list[Image.Image] = []
    gen_device = "cuda" if device_name == "cuda" else "cpu"
    for seed in seeds:
        gen = torch.Generator(device=gen_device).manual_seed(seed)
        result = pipe(
            prompt,
            num_inference_steps=NUM_INFERENCE_STEPS,
            guidance_scale=GUIDANCE_SCALE,
            height=IMAGE_SIZE,
            width=IMAGE_SIZE,
            generator=gen,
        )
        images.append(result.images[0].convert("RGB"))
    return images


@_maybe_gpu_decorator
def generate_pair(prompt: str) -> tuple[list[Image.Image], list[int]]:
    """Generate 2 SD 1.5 images for Round 2 refine."""
    prompt = (prompt or "").strip()
    if not prompt:
        raise ValueError("Prompt is empty.")
    seeds = list(REFINE_SEEDS)
    images = _generate_impl(prompt, tuple(seeds))
    return images, seeds


@_maybe_gpu_decorator
def generate_variants(prompt: str, num_variants: int = NUM_VARIANTS) -> tuple[list[Image.Image], list[int]]:
    """Generate `num_variants` SD 1.5 images from a text prompt."""
    prompt = (prompt or "").strip()
    if not prompt:
        raise ValueError("Prompt is empty — upload an anchor or type a description.")
    seeds = list(VARIANT_SEEDS[:num_variants])
    images = _generate_impl(prompt, tuple(seeds))
    return images, seeds
