# PDF OCR 功能说明

## 概述

本项目新增了基于 PaddleOCR PP-Structure 的 PDF 文档智能识别功能，支持：

- 📄 **文本识别**：高精度文本提取
- 📊 **表格识别**：自动识别表格结构并输出 HTML
- 🔢 **公式识别**：支持数学公式的 LaTeX 格式输出  
- 📐 **版面分析**：智能识别文档布局（标题、段落、图片等）
- 🔄 **文档矫正**：自动检测和矫正文档方向

## 集成的高级模型

1. **PP-LCNet_x1_0_doc_ori** - 文档方向分类
2. **PP-DocLayout-M** - 文档版面分析
3. **SLANet** - 表格结构识别
4. **UniMERNet** - 公式识别
5. **PP-OCRv5** - 文本检测和识别

## API 接口

### 1. 通过 URL 识别 PDF

**端点**: `GET /pdf/predict-by-url`

**参数**:
- `pdf_url` (string, required): PDF 文件的 URL 地址

**示例**:
```bash
curl -X GET "http://localhost:8000/pdf/predict-by-url?pdf_url=https://example.com/document.pdf"
```

### 2. 上传 PDF 文件识别

**端点**: `POST /pdf/predict-by-file`

**参数**:
- `file` (file, required): PDF 文件

**示例**:
```bash
curl -X POST "http://localhost:8000/pdf/predict-by-file" \
  -F "file=@/path/to/your/document.pdf"
```

## 返回格式

```json
{
  "resultcode": 200,
  "message": "Success",
  "data": [
    {
      "page": 1,
      "type": "text",
      "bbox": [100, 200, 500, 250],
      "text": "识别的文本内容",
      "html": "",
      "confidence": 0.98
    },
    {
      "page": 1,
      "type": "table",
      "bbox": [100, 300, 600, 500],
      "text": "表格文本内容",
      "html": "<table><tr><td>单元格1</td></tr></table>",
      "confidence": 0.95
    },
    {
      "page": 2,
      "type": "formula",
      "bbox": [150, 100, 450, 150],
      "text": "E = mc^2",
      "html": "",
      "confidence": 0.92
    }
  ]
}
```

## 字段说明

- `page`: 页码（从1开始）
- `type`: 区域类型
  - `text`: 普通文本
  - `title`: 标题
  - `table`: 表格
  - `formula`: 公式
  - `figure`: 图片
  - `equation`: 方程式
- `bbox`: 边界框坐标 [x1, y1, x2, y2]
- `text`: 提取的文本内容
- `html`: 表格的 HTML 结构（仅表格类型有值）
- `confidence`: 识别置信度 (0-1)

## 安装依赖

确保已安装所需的依赖：

```bash
pip install -r requirements.txt
```

主要依赖：
- `paddleocr>=3.7.0` - PaddleOCR 核心库
- `PyMuPDF>=1.23.0` - PDF 文件处理

## 环境变量

- `OCR_LANGUAGE`: OCR 语言设置，默认为 `ch`（中文）
- `OCR_DEBUG`: 调试模式，设置为 `1` 启用详细日志

## 性能优化建议

1. **首次运行**: 第一次使用时会自动下载模型文件，可能需要较长时间
2. **GPU 加速**: 如有 GPU，建议安装 `paddlepaddle-gpu` 以获得更好的性能
3. **内存管理**: 处理大型 PDF 时请确保有足够的内存
4. **并发处理**: 建议使用适当的 worker 数量来处理并发请求

## 使用示例（Python）

```python
import requests

# 方式1: 通过 URL
response = requests.get(
    "http://localhost:8000/pdf/predict-by-url",
    params={"pdf_url": "https://example.com/document.pdf"}
)
result = response.json()

# 方式2: 上传文件
with open("document.pdf", "rb") as f:
    files = {"file": ("document.pdf", f, "application/pdf")}
    response = requests.post(
        "http://localhost:8000/pdf/predict-by-file",
        files=files
    )
    result = response.json()

# 处理结果
for item in result["data"]:
    print(f"页码: {item['page']}, 类型: {item['type']}")
    print(f"内容: {item['text'][:100]}...")  # 前100个字符
    if item['type'] == 'table':
        print(f"表格HTML: {item['html']}")
```

## 故障排除

1. **模型下载失败**: 检查网络连接，或手动下载模型到指定目录
2. **内存不足**: 减小 PDF 分辨率或增加系统内存
3. **识别精度不够**: 调整图像预处理参数或使用更大的模型

## 技术支持

如有问题，请查看：
- [PaddleOCR 官方文档](https://github.com/PaddlePaddle/PaddleOCR)
- [PP-Structure 文档](https://github.com/PaddlePaddle/PaddleOCR/blob/main/ppstructure/README_ch.md)
