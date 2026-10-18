from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from split_booklet import page_order, split_booklet


class OrderingTests(unittest.TestCase):
    def test_eight_pages(self):
        spreads = [(8, 1), (2, 7), (6, 3), (4, 5)]
        result = [spreads[i][half == "right"] for i, half in page_order(4)]
        self.assertEqual(result, list(range(1, 9)))

    def test_incomplete_input(self):
        for count in (0, 1, 3):
            with self.assertRaises(ValueError):
                page_order(count)

    def test_every_half_once(self):
        for count in (2, 4, 40):
            self.assertEqual(set(page_order(count)),
                             {(i, half) for i in range(count) for half in ("left", "right")})
            self.assertEqual(len(page_order(count)), count * 2)


class PdfTests(unittest.TestCase):
    def test_content_positions_rotation_and_file_protection(self):
        from pypdf import PdfReader, PdfWriter
        from reportlab.pdfgen.canvas import Canvas

        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.pdf"
            canvas = Canvas(str(source), pagesize=(400, 300))
            for left, right in [(8, 1), (2, 7), (6, 3), (4, 5)]:
                canvas.drawString(50, 150, str(left))
                canvas.drawString(250, 150, str(right))
                canvas.showPage()
            canvas.save()

            # Exercise both existing /Rotate metadata and explicit corrections.
            for rotation in (0, 90, 180, 270):
                rotated = root / f"rotated-{rotation}.pdf"
                writer = PdfWriter()
                for page in PdfReader(source).pages:
                    page.rotate(rotation)
                    writer.add_page(page)
                writer.write(rotated)
                output = root / f"output-{rotation}.pdf"
                correction = (-rotation) % 360
                self.assertEqual(split_booklet(rotated, output, correction, correction), 8)
                for number, page in enumerate(PdfReader(output).pages, 1):
                    self.assertEqual(float(page.mediabox.width), 200)
                    self.assertEqual(float(page.mediabox.height), 300)
                    visible = []

                    def visit(text, cm, tm, font, size):
                        if page.cropbox.left <= tm[4] < page.cropbox.right:
                            visible.extend(text.split())

                    page.extract_text(visitor_text=visit)
                    self.assertEqual(visible, [str(number)])
                before = output.read_bytes()
                with self.assertRaises(ValueError):
                    split_booklet(rotated, output)
                self.assertEqual(output.read_bytes(), before)
            with self.assertRaises(ValueError):
                split_booklet(source, source)


if __name__ == "__main__":
    unittest.main()
