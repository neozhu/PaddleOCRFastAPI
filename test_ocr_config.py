# -*- coding: utf-8 -*-

import importlib
import sys
from types import SimpleNamespace


def test_ocr_router_omits_lang_when_explicit_models_are_used(monkeypatch):
    captured_kwargs = {}

    class FakePaddleOCR:
        def __init__(self, **kwargs):
            captured_kwargs.update(kwargs)

    monkeypatch.setitem(sys.modules, "paddleocr", SimpleNamespace(PaddleOCR=FakePaddleOCR))
    sys.modules.pop("routers.ocr", None)

    importlib.import_module("routers.ocr")

    assert "text_detection_model_name" in captured_kwargs
    assert "text_recognition_model_name" in captured_kwargs
    assert "lang" not in captured_kwargs


def test_pdf_ocr_router_omits_lang_when_explicit_models_are_used(monkeypatch):
    captured_kwargs = {}

    class FakePaddleOCR:
        def __init__(self, **kwargs):
            captured_kwargs.update(kwargs)

    monkeypatch.setitem(sys.modules, "paddleocr", SimpleNamespace(PaddleOCR=FakePaddleOCR))
    sys.modules.pop("routers.pdf_ocr", None)

    pdf_ocr = importlib.import_module("routers.pdf_ocr")
    pdf_ocr.get_pdf_ocr()

    assert "text_detection_model_name" in captured_kwargs
    assert "text_recognition_model_name" in captured_kwargs
    assert "lang" not in captured_kwargs
