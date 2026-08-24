"""Seeded, physically bounded underwater image augmentation."""

from __future__ import annotations

import io
import random


class UnderwaterAugmentation:
    version = "underwater_physical_aug_v1"

    def __init__(self, seed: int = 42, probability: float = 0.75) -> None:
        self.rng = random.Random(seed)
        self.probability = probability

    def __call__(self, image):
        from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

        output = image.convert("RGB")
        if self.rng.random() > self.probability:
            return output
        red, green, blue = output.split()
        red = red.point(lambda value: value * self.rng.uniform(0.48, 0.88))
        green = green.point(lambda value: value * self.rng.uniform(0.78, 1.02))
        blue = blue.point(lambda value: value * self.rng.uniform(0.86, 1.08))
        output = Image.merge("RGB", (red, green, blue))
        output = ImageEnhance.Contrast(output).enhance(self.rng.uniform(0.62, 1.05))
        output = ImageEnhance.Brightness(output).enhance(self.rng.uniform(0.68, 1.12))
        if self.rng.random() < 0.45:
            output = output.filter(ImageFilter.GaussianBlur(self.rng.uniform(0.2, 1.4)))
        overlay = Image.new("RGBA", output.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        width, height = output.size
        if self.rng.random() < 0.55:  # bounded artificial-light hotspot
            x, y = self.rng.randrange(width), self.rng.randrange(height)
            radius = self.rng.randint(max(4, min(width, height) // 10), max(5, min(width, height) // 3))
            draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(255, 245, 210, 28))
        particle_count = self.rng.randint(0, max(2, width * height // 14000))
        for _ in range(particle_count):
            x, y = self.rng.randrange(width), self.rng.randrange(height)
            radius = self.rng.randint(1, max(1, min(width, height) // 100))
            draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(210, 225, 215, self.rng.randint(20, 80)))
        if self.rng.random() < 0.15:  # small partial occlusion, never covers most of the image
            ow, oh = self.rng.randint(2, max(3, width // 6)), self.rng.randint(2, max(3, height // 6))
            x, y = self.rng.randrange(max(1, width - ow)), self.rng.randrange(max(1, height - oh))
            draw.ellipse((x, y, x + ow, y + oh), fill=(15, 45, 50, 80))
        output = Image.alpha_composite(output.convert("RGBA"), overlay).convert("RGB")
        if self.rng.random() < 0.25:
            buffer = io.BytesIO()
            output.save(buffer, format="JPEG", quality=self.rng.randint(55, 88))
            buffer.seek(0)
            output = Image.open(buffer).convert("RGB").copy()
        return output
