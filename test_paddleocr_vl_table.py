# -*- coding: utf-8 -*-
import os
import sys
import json
import re
import numpy as np
import fitz  # PyMuPDF
from typing import Dict, Any, List, Optional

# 检查必要的依赖库
try:
    from bs4 import BeautifulSoup
except ImportError:
    print("缺失依赖: bs4")
    print("请运行: pip install beautifulsoup4")
    sys.exit(1)

def check_dependencies():
    """跳过依赖检查，避免触发 PaddleOCR 的初始化副作用"""
    return True

# 全局实例
_engine_instance = None

def get_engine():
    """
    获取 PaddleOCR-VL-1.5 引擎（CPU 模式）。
    """
    global _engine_instance
    if _engine_instance is None:
        print("\n正在初始化 PaddleOCR-VL-1.5 引擎...")
        print("首次运行需要下载模型文件（约 2GB），请耐心等待...\n")
        try:
            from paddleocr import PaddleOCRVL

            _engine_instance = PaddleOCRVL(
                pipeline_version="v1.5",
                device="cpu",
                use_layout_detection=True,
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_chart_recognition=False,
                use_seal_recognition=False,
                use_ocr_for_image_block=True,
                format_block_content=True,
                merge_layout_blocks=True,
            )

            print("✓ PaddleOCR-VL-1.5 引擎初始化成功 (CPU 模式)\n")
        except Exception as e:
            print(f"✗ 引擎初始化失败: {e}")
            sys.exit(1)

    return _engine_instance

def pdf_page_to_numpy(page, target_max: int = 1600) -> np.ndarray:
    """
    修正后的 PDF 转图片函数
    1. 修复 Alpha 通道导致的 reshape 崩溃问题
    2. 提高分辨率以保证表格文字清晰
    """
    # 获取原始尺寸
    rect = page.rect
    # 提高缩放倍率，表格识别对分辨率要求较高，建议至少 2.0 或让长边达到 1600+
    zoom = target_max / max(rect.width, rect.height)
    if zoom < 1.0: zoom = 1.0 # 至少保持原大小
    
    mat = fitz.Matrix(zoom, zoom)
    
    # 关键修正：alpha=False 强制输出 RGB 三通道
    pix = page.get_pixmap(matrix=mat, alpha=False)
    
    img_array = np.frombuffer(pix.samples, dtype=np.uint8)
    try:
        img_array = img_array.reshape((pix.height, pix.width, 3))
    except ValueError:
        # 万一出问题，回退处理
        print(f"警告：图像尺寸不匹配，预期 {pix.height}x{pix.width}x3，实际字节数 {len(pix.samples)}")
        return None
    
    return img_array

def extract_tables_from_pdf(pdf_path: str) -> Dict[str, Any]:
    if not os.path.exists(pdf_path):
        return {"success": False, "error": "File not found"}

    engine = get_engine()
    tables_result = []

    prompt = """请识别并提取图片中的所有表格数据。
只返回严格的 JSON，不要任何额外说明文字。
格式：
[
  {
    "headers": ["列名1", "列名2", ...],
    "rows": [
      ["数据1", "数据2", ...],
      ...
    ]
  }
]
如果没有表格，请返回空数组 []。"""

    try:
        with fitz.open(pdf_path) as doc:
            for page_index, page in enumerate(doc):
                print(f"正在处理第 {page_index + 1} 页...")
                img = pdf_page_to_numpy(page)
                if img is None:
                    continue

                result = engine.predict(
                    input=img,
                    prompt=prompt,
                    max_pixels=1024 * 1024,
                    max_new_tokens=1024,
                    skip_special_tokens=True,
                )

                page_tables = []
                # PaddleOCR-VL 返回列表
                if isinstance(result, list) and result:
                    item = result[0]
                    if isinstance(item, dict):
                        # 优先解析 table_res_list
                        table_list = item.get("table_res_list") or []
                        for table_item in table_list:
                            if isinstance(table_item, dict):
                                html_code = table_item.get("pred_html") or table_item.get("html", "")
                                if html_code:
                                    table_data = parse_html_table(html_code)
                                    if table_data:
                                        page_tables.append({
                                            "page": page_index + 1,
                                            "bbox": table_item.get("bbox", []),
                                            "table": table_data,
                                        })

                        # 如果没有 HTML，尝试用 VLM 输出
                        if not page_tables:
                            response_text = str(item)
                            table_data = parse_table_response(response_text)
                            if table_data:
                                if isinstance(table_data, dict) and "headers" in table_data:
                                    page_tables.append({
                                        "page": page_index + 1,
                                        "table": table_data,
                                    })
                                elif isinstance(table_data, dict) and "data" in table_data:
                                    for t in table_data["data"]:
                                        if isinstance(t, dict) and "headers" in t:
                                            page_tables.append({
                                                "page": page_index + 1,
                                                "table": t,
                                            })
                    else:
                        response_text = item if isinstance(item, str) else str(item)
                        table_data = parse_table_response(response_text)
                        if table_data:
                            if isinstance(table_data, dict) and "headers" in table_data:
                                page_tables.append({
                                    "page": page_index + 1,
                                    "table": table_data,
                                })

                if page_tables:
                    tables_result.extend(page_tables)
                    print(f"  - 发现 {len(page_tables)} 个表格")
                else:
                    print("  - 未检测到表格")

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

    return {
        "success": True,
        "file": os.path.basename(pdf_path),
        "total_tables": len(tables_result),
        "tables": tables_result,
    }

def parse_markdown_table(md_content: str) -> Optional[Dict[str, Any]]:
    lines = [line.strip() for line in md_content.splitlines() if line.strip()]
    if len(lines) < 2:
        return None
    # 找到分隔行
    sep_idx = None
    for i, line in enumerate(lines):
        if "|" in line and ("---" in line or ":-" in line or "-:" in line):
            sep_idx = i
            break
    if sep_idx is None or sep_idx == 0:
        return None
    headers = [c.strip() for c in lines[sep_idx - 1].strip("|").split("|")]
    rows = []
    for line in lines[sep_idx + 1:]:
        if "|" not in line:
            continue
        rows.append([c.strip() for c in line.strip("|").split("|")])
    return {
        "headers": headers,
        "rows": rows,
        "total_rows": len(rows),
        "total_cols": len(headers),
    }

def parse_table_response(response: str) -> Optional[Dict[str, Any]]:
    if not response or not response.strip():
        return None
    response = response.strip()

    if "无表格" in response and "|" not in response and "<table" not in response.lower():
        return None

    # 提取代码块
    fenced_blocks = re.findall(r"```(?:json|html|markdown)?\n([\s\S]*?)\n```", response, re.IGNORECASE)
    if fenced_blocks:
        response = fenced_blocks[0].strip()

    # JSON 解析
    json_candidate = None
    if "{" in response and "}" in response:
        json_candidate = response[response.find("{"):response.rfind("}") + 1]
    elif "[" in response and "]" in response:
        json_candidate = response[response.find("["):response.rfind("]") + 1]
    if json_candidate:
        try:
            data = json.loads(json_candidate)
            if isinstance(data, dict):
                return data
            if isinstance(data, list):
                return {"data": data}
        except json.JSONDecodeError:
            pass

    # HTML 解析
    if "<table" in response.lower():
        match = re.search(r"<table[\s\S]*?</table>", response, re.IGNORECASE)
        html_block = match.group(0) if match else response
        return parse_html_table(html_block)

    # Markdown 解析
    if "|" in response and "---" in response:
        return parse_markdown_table(response)

    return None

def parse_html_table(html_content: str) -> Optional[Dict[str, Any]]:
    """解析 HTML 表格 (复用你原本的逻辑)"""
    if not html_content: return None
    soup = BeautifulSoup(html_content, 'html.parser')
    
    headers = []
    rows = []
    
    # 查找所有行
    tr_list = soup.find_all('tr')
    for tr in tr_list:
        # 尝试查找表头
        th_list = tr.find_all('th')
        td_list = tr.find_all('td')
        
        row_data = []
        if th_list:
            row_data = [t.get_text(strip=True) for t in th_list]
            if not headers: headers = row_data # 第一行包含 th 视为表头
            else: rows.append(row_data) # 后续如果还有 th 可能是复杂表头，暂作数据行
        elif td_list:
            row_data = [t.get_text(strip=True) for t in td_list]
            rows.append(row_data)
            
    # 如果没找到 th 标签，把第一行当表头
    if not headers and rows:
        headers = rows.pop(0)
        
    return {
        "headers": headers,
        "rows": rows,
        "total_rows": len(rows),
        "total_cols": len(headers) if headers else 0
    }

# 主函数保持类似结构...
if __name__ == "__main__":
    check_dependencies()
        
    # 建议使用相对路径或从命令行获取
    target_file = "Products.pdf" 
    if len(sys.argv) > 1:
        target_file = sys.argv[1]
        
    if os.path.exists(target_file):
        res = extract_tables_from_pdf(target_file)
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print(f"未找到文件: {target_file}")