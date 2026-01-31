import sys
sys.path.insert(0, 'D:/github/PaddleOCRFastAPI')

from routers.pdf_ocr import get_pdf_ocr, pdf_to_images, extract_pdf_ocr_data
import os
import json

pdf_path = 'Products.pdf'

print('=== 转换 PDF ===')
image_files = pdf_to_images(pdf_path)
print(f'生成 {len(image_files)} 页\n')

ocr = get_pdf_ocr()

all_results = []
for img_info in image_files:
    print(f'=== 处理第 {img_info["page_num"]} 页 ===')
    result = ocr.predict(input=img_info['path'])
    page_data = extract_pdf_ocr_data(result, img_info['page_num'])
    
    if page_data is not None:
        all_results.append(page_data)
        print(f'✓ 检测到表格')
        print(f'  表头: {page_data["table"]["headers"]}')
        print(f'  数据行数: {len(page_data["table"]["rows"])}')
        print(f'\n前3行数据:')
        for i, row in enumerate(page_data["table"]["rows"][:3], 1):
            print(f'  {i}. {row}')
    else:
        print(f'✗ 未检测到表格')
    print()

# 清理临时文件
for img_info in image_files:
    try:
        os.unlink(img_info['path'])
    except:
        pass

print('=== 最终结果 ===')
print(f'共提取到 {len(all_results)} 个表格\n')
print(json.dumps(all_results, indent=2, ensure_ascii=False))

print('\n✓ 测试完成')
