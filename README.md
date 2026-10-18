# Split booklet scans

Split each scanned sheet side down its vertical midpoint and restore reading
order, preserving the original images without resampling or JPEG recompression.
Requires Python 3 and pypdf:

```sh
sudo apt install python3-pypdf
python3 split_booklet.py scan.pdf
```

The default output is `scan-reading.pdf`. An optional second positional argument
sets the output path. Existing files are never overwritten.

Scan both sides of each sheet, proceeding from the outside inward:
outer front, outer back, next front, next back, and so on. Keep blank sides.
All spreads should be upright, with the front cover on the right of the first
spread. The script assumes a single left-bound booklet, not multiple signatures
or a stack scanned with all fronts followed by all backs.

For an eight-page booklet, the upright input spreads are `[8|1]`, `[2|7]`,
`[6|3]`, `[4|5]`. The script takes alternating right/left halves going inward,
then the remaining halves going outward. Covers and blank pages are retained.
An odd number of scanned sides is rejected as an incomplete sheet pair.

## Manual rotation

If front sides need 90 degrees clockwise rotation and back sides need
270 degrees clockwise rotation:

```sh
python3 split_booklet.py scan.pdf reading.pdf --front-rotation 90 --back-rotation 270
```

Front sides are input pages 1, 3, 5, ...; back sides are input pages 2, 4, 6, ...

For scans already rotated upright by scanning software, omit both rotation
options. For upright fronts with upside-down backs, use `--back-rotation 180`.
Corrections are added to any existing PDF rotation metadata, then the visible
page is split into equal halves. No OCR or automatic orientation detection is
performed. The split assumes the fold is centered; skew and off-center scans
should be corrected beforehand. Cropping controls the visible page area; it
does not redact the hidden half from the underlying PDF content.

## Tests

Tests generate their own sample PDFs; no scanned documents are included.

```sh
sudo apt install python3-reportlab
python3 -m unittest -v
```

## Automatic orientation with OCRmyPDF

OCRmyPDF can correct the scanned spreads before this script splits them. On
Ubuntu, the relevant packages are `ocrmypdf`, `tesseract-ocr`, and
`tesseract-ocr-osd`. Install them with:

```sh
sudo apt install ocrmypdf tesseract-ocr tesseract-ocr-osd
```

The following command needs OCRmyPDF 14.1 or newer:

```sh
ocrmypdf --rotate-pages --rotate-pages-threshold 8 \
  --tesseract-timeout 0 --output-type pdf --optimize 0 \
  scan.pdf upright.pdf
python3 split_booklet.py upright.pdf reading.pdf
```

Keep `--tesseract-timeout 0`: it disables text recognition while allowing
orientation detection. This workflow does not add searchable text; OCR is
handled by a separate workflow.
Standard PDF output and disabled optimization avoid PDF/A conversion and image
optimization. No deskewing or cleanup is requested.

The confidence threshold is not a percentage. The default threshold of 14
left 21 of a test booklet's 40 sides sideways, even though all 40 detected
directions matched visual inspection (minimum confidence 9.96). A threshold
of 8 permits those corrections, but is not guaranteed for other documents.
Review the rotation log and output; blank or sparse pages may remain unrotated,
and lowering the threshold can permit wrong rotations. OCRmyPDF does not infer
missing orientations from the front/back pattern. Use the script's explicit
rotation flags on the original scan when its alternating orientation is known.

See the [OCRmyPDF cookbook](https://ocrmypdf.readthedocs.io/en/v15.0.2/cookbook.html).

The threshold-8 automatic pipeline was tested on that booklet: all 80 output
pages rendered identically to the manually rotated output at a preview size
of 650 pixels on the longest edge.

Ubuntu's `bookletimposer` package also has a `--linearize` mode designed to
split booklet spreads and restore reading order. Version 0.3.1-4ubuntu1 was
tested here. It rejected OCRmyPDF's rotated PDF as incompatible with a 2x1
layout; normalizing PDF rotation into the page content first let it produce
80 pages. It also defaults to A4 output instead of the original half-sheet
size. The OCRmyPDF-plus-script workflow above avoids those additional steps.
