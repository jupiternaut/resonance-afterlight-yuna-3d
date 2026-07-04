#!/usr/bin/env python3
"""Create a minimal glTF/GLB proxy from a transparent character cutout.

This is a blockout/runtime preview asset, not a skinned production mesh.
The generated GLB embeds the RGBA PNG as a double-sided alpha-blended plane
with the origin at the character's feet.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import struct

from PIL import Image


def _pad4(data: bytes, pad: bytes = b"\x00") -> bytes:
    extra = (-len(data)) % 4
    return data + pad * extra


def _append(blob: bytearray, data: bytes) -> tuple[int, int]:
    offset = len(blob)
    blob.extend(_pad4(data))
    return offset, len(data)


def build_proxy(input_png: Path, output_glb: Path, height_m: float, name: str) -> None:
    image = Image.open(input_png).convert("RGBA")
    width_px, height_px = image.size
    aspect = width_px / height_px
    width_m = height_m * aspect

    positions = [
        -width_m / 2, 0.0, 0.0,
        width_m / 2, 0.0, 0.0,
        width_m / 2, height_m, 0.0,
        -width_m / 2, height_m, 0.0,
    ]
    normals = [0.0, 0.0, 1.0] * 4
    texcoords = [
        0.0, 1.0,
        1.0, 1.0,
        1.0, 0.0,
        0.0, 0.0,
    ]
    indices = [0, 1, 2, 0, 2, 3]

    bin_blob = bytearray()
    pos_offset, pos_len = _append(bin_blob, struct.pack("<12f", *positions))
    nrm_offset, nrm_len = _append(bin_blob, struct.pack("<12f", *normals))
    uv_offset, uv_len = _append(bin_blob, struct.pack("<8f", *texcoords))
    idx_offset, idx_len = _append(bin_blob, struct.pack("<6H", *indices))
    png_offset, png_len = _append(bin_blob, input_png.read_bytes())

    gltf = {
        "asset": {
            "version": "2.0",
            "generator": "Resonance Afterlight proxy GLB generator"
        },
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"name": name, "mesh": 0}],
        "meshes": [{
            "name": f"{name}_proxy_plane",
            "primitives": [{
                "attributes": {
                    "POSITION": 0,
                    "NORMAL": 1,
                    "TEXCOORD_0": 2
                },
                "indices": 3,
                "material": 0
            }]
        }],
        "materials": [{
            "name": f"{name}_rgba_alpha",
            "pbrMetallicRoughness": {
                "baseColorTexture": {"index": 0},
                "metallicFactor": 0.0,
                "roughnessFactor": 0.72
            },
            "alphaMode": "BLEND",
            "doubleSided": True
        }],
        "textures": [{"sampler": 0, "source": 0}],
        "samplers": [{
            "magFilter": 9729,
            "minFilter": 9987,
            "wrapS": 33071,
            "wrapT": 33071
        }],
        "images": [{
            "name": f"{name}_basecolor_rgba",
            "mimeType": "image/png",
            "bufferView": 4
        }],
        "buffers": [{"byteLength": len(bin_blob)}],
        "bufferViews": [
            {"buffer": 0, "byteOffset": pos_offset, "byteLength": pos_len, "target": 34962},
            {"buffer": 0, "byteOffset": nrm_offset, "byteLength": nrm_len, "target": 34962},
            {"buffer": 0, "byteOffset": uv_offset, "byteLength": uv_len, "target": 34962},
            {"buffer": 0, "byteOffset": idx_offset, "byteLength": idx_len, "target": 34963},
            {"buffer": 0, "byteOffset": png_offset, "byteLength": png_len}
        ],
        "accessors": [
            {
                "bufferView": 0,
                "componentType": 5126,
                "count": 4,
                "type": "VEC3",
                "min": [-width_m / 2, 0.0, 0.0],
                "max": [width_m / 2, height_m, 0.0]
            },
            {"bufferView": 1, "componentType": 5126, "count": 4, "type": "VEC3"},
            {"bufferView": 2, "componentType": 5126, "count": 4, "type": "VEC2"},
            {"bufferView": 3, "componentType": 5123, "count": 6, "type": "SCALAR"}
        ]
    }

    json_chunk = _pad4(json.dumps(gltf, separators=(",", ":")).encode("utf-8"), b" ")
    bin_chunk = _pad4(bytes(bin_blob))
    total_length = 12 + 8 + len(json_chunk) + 8 + len(bin_chunk)

    output_glb.parent.mkdir(parents=True, exist_ok=True)
    with output_glb.open("wb") as f:
        f.write(struct.pack("<4sII", b"glTF", 2, total_length))
        f.write(struct.pack("<I4s", len(json_chunk), b"JSON"))
        f.write(json_chunk)
        f.write(struct.pack("<I4s", len(bin_chunk), b"BIN\x00"))
        f.write(bin_chunk)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--height-m", type=float, default=1.68)
    parser.add_argument("--name", default="character")
    args = parser.parse_args()
    build_proxy(args.input, args.out, args.height_m, args.name)


if __name__ == "__main__":
    main()
