.PHONY: all clean

default:

# Keep source scans and finished PDFs in the project directory.
clean:
	rm -rf -- __pycache__ tmp/pdfs output/pdf
