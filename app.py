import os
import zipfile
import tempfile
import gradio as gr
import pandas as pd
from PIL import Image
from imposition import calculate_imposition
from exporter import export_to_pdf, export_to_pptx


def process_uploaded_files(files_or_zip):
    """
    Extracts or collects image file paths from uploaded file(s) or ZIP archive.
    Includes path traversal checks for ZIP extraction safety.
    """
    if not files_or_zip:
        return []

    extracted_paths = []
    
    # Handle single or multiple inputs from Gradio
    file_list = files_or_zip if isinstance(files_or_zip, list) else [files_or_zip]
    
    for f in file_list:
        file_path = f.name if hasattr(f, 'name') else str(f)
        if file_path.lower().endswith('.zip'):
            temp_dir = tempfile.mkdtemp(prefix="book_imgs_")
            try:
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    # Prevent Zip Slip / directory traversal
                    real_temp_dir = os.path.realpath(temp_dir)
                    for member in zip_ref.infolist():
                        target_path = os.path.realpath(os.path.join(temp_dir, member.filename))
                        if not target_path.startswith(real_temp_dir + os.sep) and target_path != real_temp_dir:
                            raise ValueError(f"Illegal path in ZIP archive: {member.filename}")
                        zip_ref.extract(member, temp_dir)

                    for root, _, filenames in os.walk(temp_dir):
                        for fname in sorted(filenames):
                            if fname.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff')):
                                extracted_paths.append(os.path.join(root, fname))
            except Exception as e:
                print(f"Error reading ZIP file: {e}")
        else:
            if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff')):
                extracted_paths.append(file_path)

    return sorted(extracted_paths)


def update_layout_preview(files, rows, cols, rotate_back):
    """
    Computes layout and returns a summary Markdown and DataFrame for preview.
    """
    image_paths = process_uploaded_files(files)
    total_images = len(image_paths)

    layout_data = calculate_imposition(image_paths if total_images > 0 else 0, rows=int(rows), cols=int(cols), rotate_back=rotate_back)

    summary = (
        f"**Total Images:** {layout_data['total_images']} | "
        f"**Grid Size:** {layout_data['rows']}×{layout_data['cols']} ({layout_data['images_per_side']} per side) | "
        f"**Total Physical Sheets:** {layout_data['total_sheets']} | "
        f"**Total Logical Page Sides:** {layout_data['total_logical_pages']}"
    )

    table_rows = []
    for sheet in layout_data['sheets']:
        s_num = sheet['sheet_number']
        
        # Front side summary
        front_items = sheet['front']['items']
        front_names = [os.path.basename(p) if isinstance(p, str) else ("Empty" if p is None else str(p)) for p in front_items]
        table_rows.append({
            "Sheet": s_num,
            "Side": "Front",
            "Logical Pages": sheet['front']['logical_page_number'],
            "Rotated 180°": sheet['front']['rotate_180'],
            "Grid Images": ", ".join(front_names)
        })
        
        # Back side summary
        back_items = sheet['back']['items']
        back_names = [os.path.basename(p) if isinstance(p, str) else ("Empty" if p is None else str(p)) for p in back_items]
        table_rows.append({
            "Sheet": s_num,
            "Side": "Back",
            "Logical Pages": sheet['back']['logical_page_number'],
            "Rotated 180°": sheet['back']['rotate_180'],
            "Grid Images": ", ".join(back_names)
        })
        
    df = pd.DataFrame(table_rows) if table_rows else pd.DataFrame(columns=["Sheet", "Side", "Logical Pages", "Rotated 180°", "Grid Images"])
    return summary, df


def generate_export_pdf(files, rows, cols, rotate_back):
    image_paths = process_uploaded_files(files)
    if not image_paths:
        return None, "✗ Please upload image files or a ZIP archive first."
    
    layout_data = calculate_imposition(image_paths, rows=int(rows), cols=int(cols), rotate_back=rotate_back)
    out_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name
    export_to_pdf(layout_data, out_pdf)
    return out_pdf, "✓ PDF Export generated successfully!"


def generate_export_pptx(files, rows, cols, rotate_back):
    image_paths = process_uploaded_files(files)
    if not image_paths:
        return None, "✗ Please upload image files or a ZIP archive first."
    
    layout_data = calculate_imposition(image_paths, rows=int(rows), cols=int(cols), rotate_back=rotate_back)
    out_pptx = tempfile.NamedTemporaryFile(delete=False, suffix=".pptx").name
    export_to_pptx(layout_data, out_pptx)
    return out_pptx, "✓ PPTX Export generated successfully!"


def create_interface():
    with gr.Blocks(title="Book Pagination and Layout Application") as demo:
        gr.Markdown(
            """
            # 📖 Book Pagination & Imposition Application
            
            Upload images, configure imposition layout and grid parameters, and export print-ready PDF or PPTX files.
            """
        )
        
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 1. Upload Images")
                file_input = gr.File(
                    label="Upload Image Files or ZIP Archive",
                    file_count="multiple",
                    file_types=["image", ".zip"]
                )
                
                gr.Markdown("### 2. Layout & Imposition Configuration")
                rows_input = gr.Slider(minimum=1, maximum=10, value=2, step=1, label="Rows per Side")
                cols_input = gr.Slider(minimum=1, maximum=10, value=2, step=1, label="Columns per Side")
                rotate_back_input = gr.Checkbox(value=False, label="Rotate Back Side 180° (Duplex / Tumble Binding)")
                
                calculate_btn = gr.Button("🔄 Calculate Imposition", variant="primary")
                
            with gr.Column(scale=2):
                gr.Markdown("### 3. Imposition Plan Preview")
                summary_output = gr.Markdown("Upload images and click **Calculate Imposition** to view the layout plan.")
                table_output = gr.Dataframe(label="Sheet & Page Allocation Table", interactive=False)

                gr.Markdown("### 4. Export")
                with gr.Row():
                    pdf_btn = gr.Button("📄 Export PDF", variant="secondary")
                    pptx_btn = gr.Button("📊 Export PPTX", variant="secondary")

                status_output = gr.Textbox(label="Status", interactive=False)
                file_download = gr.File(label="Download File", interactive=False)

        # Event bindings
        calculate_btn.click(
            fn=update_layout_preview,
            inputs=[file_input, rows_input, cols_input, rotate_back_input],
            outputs=[summary_output, table_output]
        )
        
        pdf_btn.click(
            fn=generate_export_pdf,
            inputs=[file_input, rows_input, cols_input, rotate_back_input],
            outputs=[file_download, status_output]
        )
        
        pptx_btn.click(
            fn=generate_export_pptx,
            inputs=[file_input, rows_input, cols_input, rotate_back_input],
            outputs=[file_download, status_output]
        )

    return demo


if __name__ == "__main__":
    demo = create_interface()
    demo.launch(share=False)
