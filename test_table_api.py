# -*- coding: utf-8 -*-

import os
import sys
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_rows_from_html_returns_simple_two_dimensional_rows():
    from routers.table import rows_from_html

    html = """
    <table>
      <tr><th>Name</th><th>Qty</th></tr>
      <tr><td>Apple</td><td>3</td></tr>
    </table>
    """

    assert rows_from_html(html) == [["Name", "Qty"], ["Apple", "3"]]


def test_normalize_format_rejects_unsupported_format():
    from routers.table import normalize_format

    with pytest.raises(ValueError):
        normalize_format("csv")


class FakeTableResult:
    def save_to_html(self, output_dir):
        Path(output_dir, "table_1.html").write_text(
            "<table><tr><th>A</th><th>B</th></tr><tr><td>1</td><td>2</td></tr></table>",
            encoding="utf-8",
        )

    def save_to_json(self, output_dir):
        Path(output_dir, "table_1.json").write_text('{"unused": true}', encoding="utf-8")

    def save_to_xlsx(self, output_dir):
        Path(output_dir, "table_1.xlsx").write_bytes(b"xlsx-bytes")


class FakeTablePipeline:
    def predict(self, input):
        assert os.path.exists(input)
        return [FakeTableResult()]


@pytest.fixture()
def table_client(monkeypatch):
    import routers.table as table_router

    monkeypatch.setattr(table_router, "get_table_pipeline", lambda: FakeTablePipeline())
    app = FastAPI()
    app.include_router(table_router.router)
    return TestClient(app)


def test_predict_by_file_returns_raw_html(table_client):
    response = table_client.post(
        "/table/predict-by-file?format=html",
        files={"file": ("sample.png", b"image-bytes", "image/png")},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert response.text == "<table><tr><th>A</th><th>B</th></tr><tr><td>1</td><td>2</td></tr></table>"


def test_predict_by_file_returns_simple_json(table_client):
    response = table_client.post(
        "/table/predict-by-file?format=json",
        files={"file": ("sample.pdf", b"%PDF-1.4", "application/pdf")},
    )

    assert response.status_code == 200
    assert response.json() == {
        "resultcode": 200,
        "message": "Success",
        "data": {
            "html": "<table><tr><th>A</th><th>B</th></tr><tr><td>1</td><td>2</td></tr></table>",
            "rows": [["A", "B"], ["1", "2"]],
        },
    }


def test_predict_by_file_returns_single_xlsx_download(table_client):
    response = table_client.post(
        "/table/predict-by-file?format=xlsx",
        files={"file": ("sample.jpg", b"image-bytes", "image/jpeg")},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert 'filename="table_result.xlsx"' in response.headers["content-disposition"]
    assert response.content == b"xlsx-bytes"


def test_predict_by_url_downloads_source_and_returns_json(table_client, monkeypatch):
    import routers.table as table_router

    response_mock = Mock()
    response_mock.content = b"image-bytes"
    response_mock.headers = {"content-type": "image/png"}
    response_mock.raise_for_status = Mock()
    monkeypatch.setattr(table_router.requests, "get", Mock(return_value=response_mock))

    response = table_client.get("/table/predict-by-url?url=https://example.com/a.png&format=json")

    assert response.status_code == 200
    assert response.json()["data"]["rows"] == [["A", "B"], ["1", "2"]]


def test_pipeline_dependency_error_returns_readable_500(monkeypatch):
    import routers.table as table_router

    def raise_dependency_error():
        raise RuntimeError("A dependency error occurred during pipeline creation")

    monkeypatch.setattr(table_router, "get_table_pipeline", raise_dependency_error)
    app = FastAPI()
    app.include_router(table_router.router)
    client = TestClient(app, raise_server_exceptions=False)

    response = client.post(
        "/table/predict-by-file?format=json",
        files={"file": ("sample.png", b"image-bytes", "image/png")},
    )

    assert response.status_code == 500
    assert "paddlex[ocr]" in response.json()["detail"]


def test_get_table_pipeline_uses_lightweight_table_defaults(monkeypatch):
    import routers.table as table_router

    captured_kwargs = {}

    class FakePipeline:
        def __init__(self, **kwargs):
            captured_kwargs.update(kwargs)

    monkeypatch.setitem(
        sys.modules,
        "paddleocr",
        SimpleNamespace(TableRecognitionPipelineV2=FakePipeline),
    )
    monkeypatch.setattr(table_router, "_table_pipeline", None)

    assert isinstance(table_router.get_table_pipeline(), FakePipeline)
    assert captured_kwargs == {
        "use_doc_orientation_classify": False,
        "use_doc_unwarping": False,
        "text_detection_model_name": "PP-OCRv5_server_det",
        "text_recognition_model_name": "PP-OCRv5_server_rec",
    }


def test_table_router_defaults_paddlex_model_source_to_modelscope(monkeypatch):
    import routers.table as table_router

    monkeypatch.delenv("PADDLE_PDX_MODEL_SOURCE", raising=False)

    table_router.configure_paddlex_model_source()

    assert os.environ["PADDLE_PDX_MODEL_SOURCE"] == "modelscope"


def test_main_wires_table_router_without_changing_existing_routes():
    main_source = Path("main.py").read_text(encoding="utf-8")

    assert "from routers import ocr, pdf_ocr, table" in main_source
    assert "app.include_router(table.router)" in main_source
