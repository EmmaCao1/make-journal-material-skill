#!/usr/bin/env python3
"""Remove a solid chroma key and create an exact 1920x1080 transparent PNG."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
from statistics import median
import sys

try:
    from PIL import Image, ImageFilter
except ImportError:
    raise SystemExit(
        "Pillow is required. Install this skill's dependency with: "
        "python -m pip install -r requirements.txt"
    )


WIDTH = 1920
HEIGHT = 1080
RGB = tuple[int, int, int]


def parse_color(value: str) -> RGB:
    match = re.fullmatch(r"#?([0-9a-fA-F]{6})", value.strip())
    if not match:
        raise argparse.ArgumentTypeError("expected a hex color such as #ff00ff")
    raw = match.group(1)
    return tuple(int(raw[index : index + 2], 16) for index in (0, 2, 4))  # type: ignore[return-value]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert a flat chroma-key image to a 1920x1080 transparent PNG."
    )
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--key-color",
        type=parse_color,
        default=None,
        help="Explicit key color. By default, estimate the key color from the outer border.",
    )
    parser.add_argument("--transparent-threshold", type=int, default=12)
    parser.add_argument("--opaque-threshold", type=int, default=220)
    parser.add_argument(
        "--edge-contract",
        type=int,
        default=0,
        choices=range(0, 5),
        metavar="0-4",
        help="Contract the alpha matte to remove a remaining colored fringe.",
    )
    parser.add_argument(
        "--no-despill",
        action="store_true",
        help="Keep original edge colors instead of removing key-color contamination.",
    )
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    if not args.input.is_file():
        raise SystemExit(f"Input image not found: {args.input}")
    if args.output.suffix.lower() != ".png":
        raise SystemExit("Output must use the .png extension.")
    if not 0 <= args.transparent_threshold <= 255:
        raise SystemExit("--transparent-threshold must be between 0 and 255.")
    if not 0 <= args.opaque_threshold <= 255:
        raise SystemExit("--opaque-threshold must be between 0 and 255.")
    if args.transparent_threshold >= args.opaque_threshold:
        raise SystemExit("--transparent-threshold must be lower than --opaque-threshold.")


def estimate_border_color(image: Image.Image) -> RGB:
    rgb = image.convert("RGB")
    width, height = rgb.size
    stride = max(1, min(width, height) // 256)
    band = max(1, min(width, height, 6))
    samples: list[RGB] = []
    for x in range(0, width, stride):
        for y in range(band):
            samples.extend((rgb.getpixel((x, y)), rgb.getpixel((x, height - 1 - y))))
    for y in range(0, height, stride):
        for x in range(band):
            samples.extend((rgb.getpixel((x, y)), rgb.getpixel((width - 1 - x, y))))
    return tuple(int(median(channel)) for channel in zip(*samples))  # type: ignore[return-value]


def smoothstep_alpha(distance: int, transparent: int, opaque: int) -> int:
    if distance <= transparent:
        return 0
    if distance >= opaque:
        return 255
    ratio = (distance - transparent) / (opaque - transparent)
    ratio = ratio * ratio * (3.0 - 2.0 * ratio)
    return round(255 * ratio)


def spill_channels(key: RGB) -> list[int]:
    strongest = max(key)
    if strongest < 128:
        return []
    return [index for index, value in enumerate(key) if value >= strongest - 16]


def dominance_alpha(rgb: RGB, key: RGB) -> int:
    spill = spill_channels(key)
    if not spill:
        return 255
    remaining = [index for index in range(3) if index not in spill]
    key_strength = min(rgb[index] for index in spill)
    foreground_strength = max((rgb[index] for index in remaining), default=0)
    dominance = key_strength - foreground_strength
    if dominance <= 0:
        return 255
    denominator = max(1, max(key) - foreground_strength)
    return max(0, min(255, round(255 * (1 - min(1, dominance / denominator)))))


def is_key_like(rgb: RGB, key: RGB, distance: int) -> bool:
    if distance <= 32:
        return True
    spill = spill_channels(key)
    if not spill:
        return False
    remaining = [index for index in range(3) if index not in spill]
    key_strength = min(rgb[index] for index in spill)
    foreground_strength = max((rgb[index] for index in remaining), default=0)
    return key_strength - foreground_strength >= 16


def remove_spill(rgb: RGB, key: RGB, alpha: int) -> RGB:
    if alpha >= 252:
        return rgb
    spill = spill_channels(key)
    if not spill:
        return rgb
    channels = list(rgb)
    remaining = [index for index in range(3) if index not in spill]
    if remaining:
        cap = max(0, max(channels[index] for index in remaining) - 1)
        for index in spill:
            channels[index] = min(channels[index], cap)
    return tuple(channels)  # type: ignore[return-value]


def remove_chroma(
    source: Image.Image,
    key: RGB,
    transparent: int,
    opaque: int,
    despill: bool,
    edge_contract: int,
) -> Image.Image:
    image = source.convert("RGBA")
    pixels = image.load()
    for y in range(image.height):
        for x in range(image.width):
            red, green, blue, source_alpha = pixels[x, y]
            distance = max(abs(red - key[0]), abs(green - key[1]), abs(blue - key[2]))
            rgb = (red, green, blue)
            key_like = is_key_like(rgb, key, distance)
            matte_alpha = (
                min(
                    smoothstep_alpha(distance, transparent, opaque),
                    dominance_alpha(rgb, key),
                )
                if key_like
                else 255
            )
            alpha = round(matte_alpha * source_alpha / 255)
            if 0 < alpha <= 8:
                alpha = 0
            if alpha == 0:
                pixels[x, y] = (0, 0, 0, 0)
                continue
            if despill and key_like:
                red, green, blue = remove_spill(rgb, key, alpha)
            pixels[x, y] = (red, green, blue, alpha)

    if edge_contract:
        alpha = image.getchannel("A")
        for _ in range(edge_contract):
            alpha = alpha.filter(ImageFilter.MinFilter(3))
        image.putalpha(alpha)
    return image


def fit_to_canvas(image: Image.Image) -> Image.Image:
    scale = min(WIDTH / image.width, HEIGHT / image.height)
    size = (max(1, round(image.width * scale)), max(1, round(image.height * scale)))
    resized = image.resize(size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    offset = ((WIDTH - size[0]) // 2, (HEIGHT - size[1]) // 2)
    canvas.alpha_composite(resized, offset)
    return canvas


def validate_output(image: Image.Image) -> None:
    alpha = image.getchannel("A")
    alpha_min, alpha_max = alpha.getextrema()
    if alpha_min != 0:
        raise SystemExit("Output has no transparent pixels. Check the selected key color.")
    if alpha_max == 0 or alpha.getbbox() is None:
        raise SystemExit("Output is fully transparent. Check the selected key color.")
    corners = ((0, 0), (WIDTH - 1, 0), (0, HEIGHT - 1), (WIDTH - 1, HEIGHT - 1))
    if any(image.getpixel(point)[3] for point in corners):
        raise SystemExit("Transparent-corner validation failed.")


def main() -> None:
    args = parse_args()
    validate_args(args)
    with Image.open(args.input) as source:
        key = args.key_color if args.key_color is not None else estimate_border_color(source)
        transparent = remove_chroma(
            source,
            key=key,
            transparent=args.transparent_threshold,
            opaque=args.opaque_threshold,
            despill=not args.no_despill,
            edge_contract=args.edge_contract,
        )
    final = fit_to_canvas(transparent)
    validate_output(final)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    final.save(args.output, format="PNG", optimize=True)
    print(
        f"Saved {args.output} ({WIDTH}x{HEIGHT}, RGBA, transparent corners; "
        f"key=#{key[0]:02x}{key[1]:02x}{key[2]:02x})"
    )


if __name__ == "__main__":
    main()
