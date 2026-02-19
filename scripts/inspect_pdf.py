from pypdf import PdfReader
import os

pdf_path = "/Users/nogashlomi/projects/yossi/SIEPM_mateirals_and_data/SIEPM_1.pdf"

if not os.path.exists(pdf_path):
    print(f"Error: File not found at {pdf_path}")
    exit(1)

reader = PdfReader(pdf_path)
print(f"Number of pages: {len(reader.pages)}")

# Print text from first 3 pages
for i in range(min(3, len(reader.pages))):
    print(f"\n--- Page {i+1} ---\n")
    print(reader.pages[i].extract_text())
