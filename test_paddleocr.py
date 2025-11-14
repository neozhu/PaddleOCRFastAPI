#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""测试 PaddleOCR 3.3.2 初始化和功能"""

def test_paddleocr_init():
    """测试 PaddleOCR 初始化"""
    try:
        from paddleocr import PaddleOCR
        print("正在初始化 PaddleOCR 3.3.2...")
        
        # 使用稳定配置初始化（3.3.2 版本）
        ocr = PaddleOCR(
            use_textline_orientation=False,  # 新版本参数
            lang='ch'
        )
        print("✓ PaddleOCR 3.3.2 初始化成功")
        return True
        
    except Exception as e:
        print(f"✗ PaddleOCR 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("测试 PaddleOCR 3.3.2 版本")
    print("=" * 60)
    
    if test_paddleocr_init():
        print("\n✓ 测试通过！PaddleOCR 3.3.2 可以正常使用")
    else:
        print("\n✗ 测试失败！")
