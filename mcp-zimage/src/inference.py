import torch
from diffusers import DiffusionPipeline
import logging

logger = logging.getLogger(__name__)


class ZImagePipeline:
    def __init__(self, model_id: str = "Tongyi-MAI/Z-Image"):
        self.model_id = model_id
        self.device = self._get_device()
        self.dtype = torch.bfloat16 if self.device.type in ["cuda", "mps"] else torch.float32

        logger.info(f"Initializing Z-Image pipeline on {self.device} with {self.dtype}")

        self.pipeline = DiffusionPipeline.from_pretrained(
            self.model_id,
            torch_dtype=self.dtype,
            device_map=None  # We will manually move to device
        )
        self.pipeline.to(self.device)

    def _get_device(self) -> torch.device:
        if torch.backends.mps.is_available():
            return torch.device("mps")
        elif torch.cuda.is_available():
            return torch.device("cuda")
        else:
            return torch.device("cpu")

    def generate(
            self,
            prompt: str,
            negative_prompt: str = "",
            num_inference_steps: int = 50,
            guidance_scale: float = 7.5,
            width: int = 1024,
            height: int = 1024,
            seed: int = -1
    ):
        """
        Generates an image from a prompt.
        """
        if seed != -1:
            generator = torch.Generator(device=self.device).manual_seed(seed)
        else:
            generator = None

        logger.info(f"#### Generating image params ####")
        logger.info(f"[prompt]: {prompt}")
        logger.info(f"[negative prompt]: {prompt}")
        logger.info(f"[resolution]: {width}x{height}")
        logger.info(f"[guidance_scale]: {guidance_scale}")
        logger.info(f"[num_inference_steps]: {num_inference_steps}")

        # Z-Image specific parameters might need adjustment based on model card
        # Using standard diffusers parameters
        output = self.pipeline(
            prompt=prompt,
            negative_prompt=negative_prompt,
            num_inference_steps=num_inference_steps,
            guidance_scale=guidance_scale,
            width=width,
            height=height,
            generator=generator
        )

        return output.images[0]
