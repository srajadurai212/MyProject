# import io
# import re
# import base64
# from PIL import Image
# import fitz  # PyMuPDF
# from markdown_pdf import MarkdownPdf, Section
# import logging

# logger = logging.getLogger(__name__)

# # -----------------------------
# # Utility: convert PIL → base64
# # -----------------------------
# def pil_to_base64(pil_img):
#     buf = io.BytesIO()
#     pil_img.save(buf, format="PNG")
#     return base64.b64encode(buf.getvalue()).decode("utf-8")


# # -----------------------------
# # Add top-right logo
# # -----------------------------

# def add_footer_logo_fixed(pdf_bytes, logo_path="int_logo.png", width=130, margin=15):
#     """
#     Adds a logo at the very bottom-right of every page.
#     Logo will always sit above the bottom margin and will NOT overlap content.
#     """
#     doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    
#     for page in doc:
#         rect = page.rect
#         # Bottom-right placement
#         x0 = rect.width - width - margin
#         y0 = rect.height - width - margin  # pinned at bottom
#         x1 = x0 + width
#         y1 = y0 + width

#         page.insert_image(
#             fitz.Rect(x0, y0, x1, y1),
#             filename=logo_path,
#             keep_proportion=True,
#             overlay=True  # draws on top without erasing content
#         )

#     out_bytes = doc.write()
#     doc.close()
#     return out_bytes



# # -----------------------------
# # PDF Generation Function
# # -----------------------------
# A4_PORTRAIT_WIDTH = 595
# A4_PORTRAIT_HEIGHT = 842
# A4_LANDSCAPE_WIDTH = 842
# A4_LANDSCAPE_HEIGHT = 595
# MIN_COL_WIDTH = 40
# MAX_FONT_SIZE = 12
# MIN_FONT_SIZE = 6
# MAX_COLUMNS_PORTRAIT = 6
# BOTTOM_PADDING_PT = 80 

# def dynamic_markdown_to_pdf(
#     markdown_text,
#     ref_img=None,
#     test_img=None,
#     output_file="output.pdf",
#     toc_level=0,
#     logo_path="int_logo.png"
# ):
#     pdf = MarkdownPdf(toc_level=toc_level, optimize=True)

#     # ----- Title -----
#     title_markdown = "# 📝 Image Comparison Report\n\n"

#     # ----- Images side by side with captions -----
#     image_markdown = ""
#     if ref_img is not None or test_img is not None:
#         # Calculate max width to fit both images in page
#         page_width = A4_PORTRAIT_WIDTH - 60  # 30pt margin on each side
#         max_img_width = page_width / 2 - 10  # 10pt spacing between images

#         table_cells = ""
#         if ref_img is not None:
#             ref_pil = Image.fromarray(ref_img)
#             ref_pil.thumbnail((max_img_width, 400))  # limit height to 400pt
#             ref_b64 = pil_to_base64(ref_pil)
#             table_cells += f'<td align="center"><img src="data:image/png;base64,{ref_b64}" width="{ref_pil.width}"><br>Reference Image</td>'

#         if test_img is not None:
#             test_pil = Image.fromarray(test_img)
#             test_pil.thumbnail((max_img_width, 400))
#             test_b64 = pil_to_base64(test_pil)
#             table_cells += f'<td align="center"><img src="data:image/png;base64,{test_b64}" width="{test_pil.width}"><br>Test Image</td>'

#         image_markdown += f'<table width="100%"><tr>{table_cells}</tr></table>\n\n'

#     # ----- Combine title + images + markdown text -----
#     final_markdown = title_markdown + image_markdown + markdown_text

#     # ----- Detect largest table for layout -----
#     tables = re.findall(r'\|.*\|', final_markdown)
#     max_cols = max([line.count('|') - 1 for line in tables], default=1)

#     # ----- Orientation & font size -----
#     if max_cols > MAX_COLUMNS_PORTRAIT:
#         paper_size = "A4-L"
#         page_width = A4_LANDSCAPE_WIDTH
#     else:
#         paper_size = "A4"
#         page_width = A4_PORTRAIT_WIDTH

#     font_size = max(
#         MIN_FONT_SIZE,
#         min(MAX_FONT_SIZE, int(page_width / max_cols / 10))
#     )
#     cell_padding = max(0.2, font_size / 12 * 0.5)

#     table_css = f"""
#     @page {{
#         margin-bottom: 120pt;  /* reserve area for logo */
#     }}
#     table {{
#         table-layout: fixed;
#         width: 100%;
#         border-collapse: collapse;
#         overflow-wrap: break-word;
#         word-wrap: break-word;
#         word-break: break-word;
#     }}
#     th, td {{
#         border: 0.5px solid black;
#         padding: {cell_padding}pt;
#         font-size: {font_size}pt;
#     }}
#     hr {{
#         border: 0.5px solid #999;
#         margin: 6pt 0;
#     }}
#     """

#     pdf.add_section(Section(final_markdown, paper_size=paper_size), user_css=table_css)

#     # ----- Save PDF to memory -----
#     pdf_bytes_io = io.BytesIO()
#     pdf.save(pdf_bytes_io)
#     pdf_bytes = pdf_bytes_io.getvalue()

#     # ----- Add logo at top-right -----
#     if logo_path:
#         pdf_bytes = add_footer_logo_fixed(pdf_bytes, logo_path=logo_path, width=100, margin=15)  # increased width

#     logger.info("Dynamic markdown + image PDF generated with bottom-right logo")
#     return pdf_bytes
