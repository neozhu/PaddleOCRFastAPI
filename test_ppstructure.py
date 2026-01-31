# -*- coding: utf-8 -*-
"""
测试 PPStructure 表格识别功能

功能：验证 PaddleOCR 的 PPStructure 模块能否正确识别 PDF 中的表格
"""

import os
import numpy as np
import fitz  # PyMuPDF
import cv2
from typing import Dict, Any
from bs4 import BeautifulSoup

try:
    from paddleocr import PPStructureV3
    print("✓ PPStructureV3 导入成功")
except ImportError as e:
    print(f"✗ PPStructureV3 导入失败: {e}")
    print("提示：可能需要安装 paddleocr>=3.0.0")
    exit(1)

# 全局实例
_table_engine = None

def get_table_engine():
    """
    获取 PP-StructureV3 表格识别实例 (单例模式)
    使用专业的表格识别模块
    """
    global _table_engine
    if _table_engine is None:
        print("\n正在初始化 PPStructureV3 引擎...")
        print("使用表格识别最小配置（禁用文档预处理与版面分析）")
        
        try:
            # PPStructureV3 是 PaddleOCR 3.x 的版面分析和表格识别模块
            # 仅启用表格识别，避免加载文档方向分类等模型
            _table_engine = PPStructureV3(
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False,
                use_table_recognition=True,
                use_chart_recognition=False,
                use_formula_recognition=False,
                use_region_detection=False
            )
            print("✓ PPStructureV3 引擎初始化成功\n")
        except Exception as e:
            print(f"✗ PPStructureV3 引擎初始化失败: {e}\n")
            raise
    
    return _table_engine


def parse_html_to_json(html_content: str) -> Dict[str, Any]:
    """
    使用 BeautifulSoup 解析 PaddleOCR 返回的 HTML 表格代码
    将其转换为结构化的 JSON 格式
    """
    if not html_content or not html_content.strip():
        return None
    
    soup = BeautifulSoup(html_content, 'html.parser')
    headers = []
    rows = []

    # 获取所有行
    tr_list = soup.find_all('tr')
    if not tr_list:
        return None

    for tr in tr_list:
        row_data = []
        # 处理表头 (th)
        th_list = tr.find_all('th')
        if th_list:
            headers = [th.get_text(strip=True) for th in th_list]
            continue
            
        # 处理数据行 (td)
        td_list = tr.find_all('td')
        if td_list:
            for td in td_list:
                # 简单处理：提取文本
                # 如果需要精确还原合并结构，需解析 rowspan/colspan
                row_data.append(td.get_text(strip=True))
            rows.append(row_data)

    # 如果 HTML 中没有 th 标签，第一行视为表头
    if not headers and rows:
        headers = rows.pop(0)

    # 简单校验：如果没有数据，视为无效表格
    if not headers and not rows:
        return None

    return {
        "headers": headers,
        "rows": rows,
        "total_rows": len(rows),
        "total_cols": len(headers)
    }


def pdf_page_to_numpy(page) -> np.ndarray:
    """
    将 PyMuPDF 页面转换为 OpenCV 格式的 numpy 数组 (BGR)
    无需保存文件到磁盘
    """
    # 2.0 表示 2倍分辨率渲染，提升小字识别率
    pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
    
    # 从内存字节流创建 numpy 数组
    # pix.samples 是 RGB 数据
    img_array = np.frombuffer(pix.samples, dtype=np.uint8)
    img_array = img_array.reshape((pix.height, pix.width, 3))
    
    # 转换为 OpenCV 需要的 BGR 格式
    img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    
    return img_bgr


def process_pdf_file(pdf_path: str):
    """
    处理 PDF 文件的核心逻辑
    """
    if not os.path.exists(pdf_path):
        print(f"✗ 文件不存在: {pdf_path}")
        return
    
    print(f"\n{'='*60}")
    print(f"开始处理 PDF: {os.path.basename(pdf_path)}")
    print(f"{'='*60}\n")
    
    engine = get_table_engine()
    results_list = []
    
    try:
        # 打开 PDF
        with fitz.open(pdf_path) as doc:
            total_pages = len(doc)
            print(f"PDF 总页数: {total_pages}\n")
            
            for page_index in range(total_pages):
                page_num = page_index + 1
                print(f"处理第 {page_num}/{total_pages} 页...")
                
                # 1. 内存中转为图片 (numpy 数组)
                img = pdf_page_to_numpy(doc[page_index])
                print(f"  - 图像尺寸: {img.shape[1]}x{img.shape[0]} (宽x高)")
                
                # 2. 调用 PP-Structure 识别
                # result 是一个列表，包含该页检测到的所有区域
                print(f"  - 调用 PPStructure 识别...")
                ocr_results = engine.predict(img)
                print(f"  - 检测到 {len(ocr_results)} 个区域")
                
                # 3. 提取表格类型的区域
                page_tables = 0
                for idx, region in enumerate(ocr_results):
                    if isinstance(region, dict):
                        # PPStructureV3 通常返回整页级别的结果，表格在 table_res_list 中
                        if 'table_res_list' in region:
                            table_list = region.get('table_res_list') or []
                            print(f"    区域 {idx+1}: table_res_list 数量={len(table_list)}")
                            
                            if not table_list:
                                print("      → 未检测到表格")
                            
                            for t_idx, table_item in enumerate(table_list, 1):
                                if isinstance(table_item, dict):
                                    html_code = table_item.get('pred_html', '') or table_item.get('html', '')
                                    if not html_code:
                                        res = table_item.get('res', {})
                                        if isinstance(res, dict):
                                            html_code = res.get('html', '')
                                    
                                    if html_code:
                                        page_tables += 1
                                        print(f"      → 表格 {t_idx}: HTML 长度={len(html_code)}")
                                        table_data = parse_html_to_json(html_code)
                                        if table_data:
                                            results_list.append({
                                                "page": page_num,
                                                "table": table_data,
                                                "bbox": table_item.get('bbox', [])
                                            })
                                            print(f"        → 表头: {table_data['headers']}")
                                            print(f"        → 数据行数: {table_data['total_rows']}")
                                            print(f"        → 列数: {table_data['total_cols']}")
                                        else:
                                            print("        → 警告: HTML 解析失败")
                                    else:
                                        print("      → 表格结果不含 HTML")
                                        print(f"        → table_item keys: {list(table_item.keys())}")
                                else:
                                    print(f"      → 表格 {t_idx}: 非字典输出，类型={type(table_item)}")
                            continue
                        
                        # 兼容旧结构：单区域类型输出
                        region_type = region.get('type') or region.get('label') or 'unknown'
                        print(f"    区域 {idx+1}: 类型={region_type}")
                        
                        res = region.get('res', {})
                        html_code = res.get('html', '') if isinstance(res, dict) else ''
                        if html_code:
                            page_tables += 1
                            print(f"      → 发现表格! HTML 长度: {len(html_code)} 字符")
                            table_data = parse_html_to_json(html_code)
                            if table_data:
                                results_list.append({
                                    "page": page_num,
                                    "table": table_data,
                                    "bbox": region.get('bbox', [])
                                })
                                print(f"      → 表头: {table_data['headers']}")
                                print(f"      → 数据行数: {table_data['total_rows']}")
                                print(f"      → 列数: {table_data['total_cols']}")
                            else:
                                print("      → 警告: HTML 解析失败")
                        else:
                            print("      → 未包含 HTML 表格结果")
                            print(f"      → region keys: {list(region.keys())}")
                            if isinstance(res, dict):
                                print(f"      → res keys: {list(res.keys())}")
                    else:
                        print(f"    区域 {idx+1}: 非字典输出，类型={type(region)}")
                
                if page_tables == 0:
                    print(f"  - 该页未检测到表格\n")
                else:
                    print(f"  - 该页共检测到 {page_tables} 个表格\n")
                    
    except Exception as e:
        import traceback
        print(f"\n✗ 处理失败:")
        traceback.print_exc()
        return None

    # 输出最终结果
    print(f"\n{'='*60}")
    print(f"处理完成!")
    print(f"{'='*60}")
    print(f"总共提取到 {len(results_list)} 个表格结构\n")
    
    if results_list:
        print("表格详情:")
        for i, result in enumerate(results_list, 1):
            print(f"\n表格 {i}:")
            print(f"  - 页码: {result['page']}")
            print(f"  - 表头: {result['table']['headers']}")
            print(f"  - 数据行: {result['table']['total_rows']} 行")
            print(f"  - 列数: {result['table']['total_cols']} 列")
            if result['table']['rows']:
                print(f"  - 第一行数据: {result['table']['rows'][0]}")
    else:
        print("未提取到任何表格")
    
    return results_list


if __name__ == "__main__":
    print("\n" + "="*60)
    print("PPStructure 表格识别测试")
    print("="*60)
    
    # 测试文件路径（请根据实际情况修改）
    test_files = [
        "D:\\github\\PaddleOCRFastAPI\\Products.pdf",
        "D:\\github\\PaddleOCRFastAPI\\1.pdf"
    ]
    
    # 查找可用的测试文件
    available_files = [f for f in test_files if os.path.exists(f)]
    
    if not available_files:
        print("\n✗ 未找到测试 PDF 文件")
        print("请将 PDF 文件放置在以下位置之一:")
        for f in test_files:
            print(f"  - {f}")
        print("\n或修改脚本中的 test_files 列表")
        exit(1)
    
    # 处理第一个可用文件
    test_file = available_files[0]
    print(f"\n使用测试文件: {test_file}")
    
    try:
        results = process_pdf_file(test_file)
        
        if results:
            print("\n" + "="*60)
            print("✓ 测试成功!")
            print("="*60)
        else:
            print("\n" + "="*60)
            print("⚠ 测试完成，但未提取到表格")
            print("="*60)
            
    except Exception as e:
        print("\n" + "="*60)
        print("✗ 测试失败!")
        print("="*60)
        import traceback
        traceback.print_exc()
