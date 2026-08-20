import os
import tempfile
from PIL import Image
from imposition import calculate_imposition
from exporter import export_to_pdf, export_to_pptx


def test_exporter_pdf_and_pptx():
    temp_dir = tempfile.mkdtemp()
    img_paths = []

    # Create 4 dummy image files
    for i in range(4):
        p = os.path.join(temp_dir, f"test_img_{i}.png")
        img = Image.new('RGB', (100, 100), color=(73 * i % 255, 100, 150))
        img.save(p)
        img_paths.append(p)

    layout_data = calculate_imposition(img_paths, rows=2, cols=2, rotate_back=True)

    pdf_out = os.path.join(temp_dir, "output.pdf")
    pptx_out = os.path.join(temp_dir, "output.pptx")

    export_to_pdf(layout_data, pdf_out)
    export_to_pptx(layout_data, pptx_out)

    assert os.path.exists(pdf_out)
    assert os.path.getsize(pdf_out) > 0

    assert os.path.exists(pptx_out)
    assert os.path.getsize(pptx_out) > 0
