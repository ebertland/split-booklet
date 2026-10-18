#!/usr/bin/env python3
"""Split duplex booklet scans into single pages in reading order."""

import argparse
from copy import copy
from pathlib import Path


def page_order(side_count):
    """Yield (source index, half) in reading order; halves are upright."""
    if side_count < 2 or side_count % 2:
        raise ValueError("Expected a positive, even number of scanned sides (two per sheet).")
    first = [(i, "right" if i % 2 == 0 else "left") for i in range(side_count)]
    last = [(i, "left" if i % 2 == 0 else "right") for i in reversed(range(side_count))]
    return first + last


def split_booklet(source, destination, front_rotation=0, back_rotation=0):
    try:
        from pypdf import PdfReader, PdfWriter
        from pypdf.generic import RectangleObject
    except ImportError as exc:
        raise ValueError("Missing pypdf. Install with: sudo apt install python3-pypdf") from exc

    source, destination = Path(source), Path(destination)
    if source.resolve() == destination.resolve():
        raise ValueError("Input and output must be different files.")
    if destination.exists():
        raise ValueError(f"Output already exists: {destination}")
    reader = PdfReader(source)
    if reader.is_encrypted:
        raise ValueError("Encrypted PDFs are not supported; supply a decrypted copy.")
    order = page_order(len(reader.pages))
    # Normalize PDF /Rotate as well as the requested corrections before cropping.
    pages = []
    for i, page in enumerate(reader.pages):
        page = copy(page)
        rotation = back_rotation if i % 2 else front_rotation
        if rotation:
            page.rotate(rotation)
        if page.rotation:
            page.transfer_rotation_to_content()
        pages.append(page)

    writer = PdfWriter()
    for index, half in order:
        page = copy(pages[index])
        left, bottom, right, top = map(float, page.cropbox)
        middle = (left + right) / 2
        bounds = (left, bottom, middle, top) if half == "left" else (middle, bottom, right, top)
        # Copy dictionaries, retaining shared image streams without recompression.
        for box in ("mediabox", "cropbox", "trimbox", "bleedbox", "artbox"):
            setattr(page, box, RectangleObject(bounds))
        writer.add_page(page)
    # Exclusive creation protects existing files, including against races.
    with destination.open("xb") as stream:
        writer.write(stream)
    return len(order)


def main():
    parser = argparse.ArgumentParser(description=__doc__, epilog=(
        "Input order: outer sheet front, outer sheet back, next sheet front, "
        "next sheet back, continuing inward. Front cover must be on the right "
        "after rotation. Keep all blank sides. Rotation values are clockwise "
        "and added to existing PDF rotation."
    ))
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path, nargs="?", help="default: INPUT-reading.pdf")
    for side in ("front", "back"):
        parser.add_argument(f"--{side}-rotation", type=int, choices=(0, 90, 180, 270), default=0,
                            help=f"additional clockwise rotation for {side} sides (default: 0)")
    args = parser.parse_args()
    destination = args.output or args.input.with_name(args.input.stem + "-reading.pdf")
    try:
        count = split_booklet(args.input, destination, args.front_rotation, args.back_rotation)
    except Exception as exc:
        parser.exit(1, f"Error: {exc}\n")
    print(f"Wrote {count} pages to {destination}")


if __name__ == "__main__":
    main()
