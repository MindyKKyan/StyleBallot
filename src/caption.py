"""Mini image captioning model — CPU draft for vision describe fallback."""

from __future__ import annotations

from PIL import Image

from .config import CAPTION_MODEL_ID

_model = None
_tokenizer = None
_image_processor = None


def _load():
    global _model, _tokenizer, _image_processor
    if _model is not None:
        return _model, _tokenizer, _image_processor
    from transformers import AutoImageProcessor, AutoTokenizer, VisionEncoderDecoderModel

    _model = VisionEncoderDecoderModel.from_pretrained(CAPTION_MODEL_ID)
    _tokenizer = AutoTokenizer.from_pretrained(CAPTION_MODEL_ID)
    _image_processor = AutoImageProcessor.from_pretrained(CAPTION_MODEL_ID)
    _model.eval()
    return _model, _tokenizer, _image_processor


def caption_image(img: Image.Image) -> str:
    model, tokenizer, image_processor = _load()
    pixel_values = image_processor(img.convert("RGB"), return_tensors="pt").pixel_values
    generated_ids = model.generate(pixel_values, num_beams=3, max_new_tokens=64)
    return tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0].strip()
