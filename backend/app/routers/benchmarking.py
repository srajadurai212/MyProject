# from fastapi import APIRouter, UploadFile, File, Form
# import json
# from image_preprocess.image_preprocessor import BaseImagePreprocessor
# from image_process.route import process_image
# from comparison_layers.low_level import low_level_compare
# from comparison_layers.high_level import high_level_check
# from models.qwen_3_8b_api import run_vlm
# from models.groq_llama_4_scout_17b import run_groq_vlm
# import json
# from fastapi import FastAPI, UploadFile, File, Form
# import uvicorn
# import cv2
# import tempfile
# from models.qwen_3_8b_api import run_vlm
# from models.groq_llama_4_scout_17b import run_groq_vlm
# from comparison_layers.low_level import low_level_compare
# from comparison_layers.high_level import high_level_check
# from image_preprocess.image_preprocessor import BaseImagePreprocessor
# from image_preprocess.utils import get_target_size
# from image_process.route import process_image
# from models.init_inspect import run_init_inspect_vlm
# from app.schemas import *
# from app.generate_pdf import dynamic_markdown_to_pdf
# from fastapi.responses import StreamingResponse
# import io
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.staticfiles import StaticFiles
# from fastapi.responses import FileResponse
# import base64

# router = APIRouter(prefix="/benchmarking", tags=["Benchmarking"])
# image_processor = BaseImagePreprocessor()

# def check_same_object_class(ref_img_path, test_img_path,):
#     image_object_details = run_init_inspect_vlm(ref_img_path, test_img_path)
#     cleaned = image_object_details.replace("```", "").strip()
#     print("image_object_details:", cleaned)
#     result = json.loads(cleaned)
#     return result

# def compare_images(ref_img_paths: list, test_img_paths: list, details:dict, model: str = "llama"):
#     """Runs preprocessing, comparison layers, and VLM response."""

#     ref_img = image_processor.load_image(ref_img_paths[0])
#     test_img = image_processor.load_image(test_img_paths[0])

#     target_size = get_target_size(ref_img, test_img)

#     print("Target size:", target_size)

#     ref_processed = []
#     test_processed = []
#     for ref_img_path in ref_img_paths:
#         ref_processed.append(image_processor.run(ref_img_path, target_size))
#     for test_img_path in test_img_paths:
#         test_processed.append(image_processor.run(test_img_path, target_size))
#     print("Preprocessing done................")

#     for i in range(len(ref_processed)):
#         ref_processed[i]["dimensions"], ref_seg_img = process_image(ref_processed[i]["processed"], details["reference_image"], image_name="Reference Image")

#     for img in range(len(test_processed)):
#         test_processed[img]["dimension"], test_seg_img = process_image(test_processed[img]["processed"], details["test_image"], image_name="Test Image")

#     low_results = low_level_compare(ref_processed[0]["grayscale"], test_processed[0]["grayscale"])
#     high_results = high_level_check(ref_processed[0]["grayscale"], test_processed[0]["grayscale"])

#     if model == "qwen":
#         vlm_output = run_vlm(
#             ref_processed,
#             test_processed,None,
#             None,)

#     elif model == "llama":
#         vlm_output = run_groq_vlm(
#             ref_processed,
#             test_processed, low_results,
#             high_results,)

#     ref_rgb = cv2.cvtColor(ref_processed[0]["processed"], cv2.COLOR_BGR2RGB)
#     test_rgb = cv2.cvtColor(test_processed[0]["processed"], cv2.COLOR_BGR2RGB)

#     ref_seg = cv2.cvtColor(ref_seg_img, cv2.COLOR_BGR2RGB)
#     test_seg = cv2.cvtColor(test_seg_img, cv2.COLOR_BGR2RGB)

#     return {
#         "ref_image": ref_rgb,
#         "test_image": test_rgb,
#         "ref_warnings": ref_processed[0]["metadata"]["warnings"],
#         "test_warnings": test_processed[0]["metadata"]["warnings"],
#         "vlm": vlm_output,
#         "ref_segmented": ref_seg,
#         "test_segmented": test_seg,
#     }


# def _save_uploads(files: list[UploadFile]) -> list[str]:
#     paths = []
#     for f in files:
#         with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
#             tmp.write(f.file.read())
#             paths.append(tmp.name)
#     return paths


# @router.post("/check-object-class")
# async def check_object_class_api(
#     reference_images: list[UploadFile] = File(...),
#     test_images: list[UploadFile] = File(...)
# ):
#     ref_paths = _save_uploads(reference_images)
#     test_paths = _save_uploads(test_images)

#     return check_same_object_class(ref_paths, test_paths)


# @router.post("/compare-images")
# async def compare_images_api(
#     reference_images: list[UploadFile] = File(...),
#     test_images: list[UploadFile] = File(...),
#     details: str = Form(...),
#     model: str = Form("llama")
# ):
#     ref_paths = _save_uploads(reference_images)
#     test_paths = _save_uploads(test_images)

#     details_dict = json.loads(details)

#     result = compare_images(
#         ref_paths,
#         test_paths,
#         details_dict,
#         model
#     )

#     # Convert numpy images → bytes (API-safe)
#     def to_bytes(img):
#         _, buffer = cv2.imencode(".png", img)
#         return buffer.tobytes()


#     def to_base64(img):
#         _, buffer = cv2.imencode(".png", img)
#         return base64.b64encode(buffer).decode("utf-8")

#     return {
#         "vlm": result["vlm"],
#         "ref_warnings": result["ref_warnings"],
#         "test_warnings": result["test_warnings"],
#         "ref_image": to_base64(result["ref_image"]),
#         "test_image": to_base64(result["test_image"]),
#         "ref_segmented": to_base64(result["ref_segmented"]),
#         "test_segmented": to_base64(result["test_segmented"]),
#     }
