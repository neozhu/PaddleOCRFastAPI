# -*- coding: utf-8 -*-

import os
import shutil
import tempfile
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable, Optional, Union
from urllib.parse import urlparse

import requests
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse, HTMLResponse

from models.RestfulModel import RestfulModel

router = APIRouter(prefix="/table", tags=["Table Recognition"])

SUPPORTED_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".pdf"}
SUPPORTED_FORMATS = {"json", "html", "xlsx"}
XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

_table_pipeline = None


def configure_paddlex_model_source() -> None:
    os.environ.setdefault("PADDLE_PDX_MODEL_SOURCE", "modelscope")


configure_paddlex_model_source()


class _TableHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows = []
        self._current_row = None
        self._current_cell = None
        self._in_cell = False

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self._current_row = []
        elif tag in {"td", "th"} and self._current_row is not None:
            self._current_cell = []
            self._in_cell = True

    def handle_data(self, data):
        if self._in_cell and self._current_cell is not None:
            text = data.strip()
            if text:
                self._current_cell.append(text)

    def handle_endtag(self, tag):
        if tag in {"td", "th"} and self._current_row is not None and self._current_cell is not None:
            self._current_row.append(" ".join(self._current_cell))
            self._current_cell = None
            self._in_cell = False
        elif tag == "tr" and self._current_row is not None:
            if self._current_row:
                self.rows.append(self._current_row)
            self._current_row = None


def normalize_format(format_value: str) -> str:
    output_format = (format_value or "json").lower()
    if output_format not in SUPPORTED_FORMATS:
        raise ValueError("format 只支持 json、html、xlsx")
    return output_format


def rows_from_html(html: str) -> list[list[str]]:
    parser = _TableHTMLParser()
    parser.feed(html or "")
    return parser.rows


def get_table_pipeline():
    global _table_pipeline
    if _table_pipeline is None:
        configure_paddlex_model_source()
        from paddleocr import TableRecognitionPipelineV2

        _table_pipeline = TableRecognitionPipelineV2(
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            text_detection_model_name="PP-OCRv6_small_det",
            text_recognition_model_name="PP-OCRv6_small_rec",
        )
    return _table_pipeline


def _suffix_from_url(source_url: str, content_type: Optional[str]) -> str:
    path_suffix = Path(urlparse(source_url).path).suffix.lower()
    if path_suffix in SUPPORTED_SUFFIXES:
        return path_suffix

    content_type = (content_type or "").lower()
    if "pdf" in content_type:
        return ".pdf"
    if "png" in content_type:
        return ".png"
    if "jpeg" in content_type or "jpg" in content_type:
        return ".jpg"
    if "bmp" in content_type:
        return ".bmp"
    if "tiff" in content_type:
        return ".tiff"
    return ""


def _suffix_from_upload(filename: str | None) -> str:
    return Path(filename or "").suffix.lower()


def _write_temp_file(content: bytes, suffix: str) -> str:
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp_file:
        tmp_file.write(content)
        return tmp_file.name


def _cleanup_paths(paths: Iterable[Union[str, Path]]) -> None:
    for path in paths:
        try:
            path_obj = Path(path)
            if path_obj.is_dir():
                shutil.rmtree(path_obj, ignore_errors=True)
            elif path_obj.exists():
                path_obj.unlink()
        except Exception:
            pass


def _first_exported_file(output_dir: str, suffix: str) -> Path:
    files = sorted(Path(output_dir).rglob(f"*{suffix}"))
    if not files:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"表格导出失败，未生成 {suffix} 文件",
        )
    return files[0]


def _first_table_result(input_path: str):
    try:
        output = get_table_pipeline().predict(input_path)
    except RuntimeError as exc:
        message = str(exc)
        if "dependency error" in message.lower() or "requires additional dependencies" in message.lower():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='表格识别依赖缺失，请安装同版本 OCR 额外依赖: pip install "paddlex[ocr]==3.7.1"',
            )
        raise
    results = list(output or [])
    if not results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未识别到表格",
        )
    return results[0]


def _export_first_table(input_path: str, output_format: str, background_tasks: BackgroundTasks):
    output_dir = tempfile.mkdtemp(prefix="table_result_")
    defer_output_cleanup = False
    try:
        table_result = _first_table_result(input_path)

        if output_format == "xlsx":
            table_result.save_to_xlsx(output_dir)
            xlsx_path = _first_exported_file(output_dir, ".xlsx")
            _cleanup_paths([input_path])
            defer_output_cleanup = True
            background_tasks.add_task(_cleanup_paths, [output_dir])
            return FileResponse(
                path=str(xlsx_path),
                media_type=XLSX_MEDIA_TYPE,
                filename="table_result.xlsx",
                background=background_tasks,
            )

        table_result.save_to_html(output_dir)
        html_path = _first_exported_file(output_dir, ".html")
        html = html_path.read_text(encoding="utf-8")

        if output_format == "html":
            return HTMLResponse(content=html)

        table_result.save_to_json(output_dir)
        return RestfulModel(
            resultcode=200,
            message="Success",
            data={
                "html": html,
                "rows": rows_from_html(html),
            },
        )
    finally:
        if not defer_output_cleanup:
            _cleanup_paths([input_path, output_dir])


@router.get("/predict-by-url", summary="识别图片或 PDF URL 中的第一个表格")
async def predict_table_by_url(
    background_tasks: BackgroundTasks,
    url: str = Query(..., description="图片或 PDF 的 URL"),
    format: str = Query("json", description="输出格式: json、html、xlsx"),
):
    try:
        output_format = normalize_format(format)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无法下载文件: {exc}",
        )

    suffix = _suffix_from_url(url, response.headers.get("content-type"))
    if suffix not in SUPPORTED_SUFFIXES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL 文件类型不支持，请使用图片或 PDF",
        )

    input_path = _write_temp_file(response.content, suffix)
    return _export_first_table(input_path, output_format, background_tasks)


@router.post("/predict-by-file", summary="识别上传图片或 PDF 中的第一个表格")
async def predict_table_by_file(
    background_tasks: BackgroundTasks,
    file: UploadFile,
    format: str = Query("json", description="输出格式: json、html、xlsx"),
):
    try:
        output_format = normalize_format(format)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    suffix = _suffix_from_upload(file.filename)
    if suffix not in SUPPORTED_SUFFIXES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请上传支持的图片或 PDF 文件",
        )

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="上传文件为空",
        )

    input_path = _write_temp_file(file_bytes, suffix)
    return _export_first_table(input_path, output_format, background_tasks)
