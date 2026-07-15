[English](./README.md)

# PaddleOCRFastAPI

一个面向实际调用场景的 FastAPI 服务：支持图片 OCR、PDF 表格提取，以及图片/PDF 的表格识别。当前依赖版本为 PaddleOCR 3.7.0、PaddleX OCR 3.7.1 和 PaddlePaddle 3.2.0；图片 OCR 使用轻量级 PP-OCRv6 检测与识别模型。

Docker 镜像基于 Python 3.12。

![PaddleOCRFastAPI 使用流程](./screenshots/api-usage-flow.png)

## 功能

- 通过上传文件、URL、Base64 数据或服务端本地路径进行图片 OCR。
- 识别上传图片/PDF 或公开图片/PDF URL 中的表格。
- 提取上传 PDF 或公开 PDF URL 中的表格数据。
- 表格识别接口支持 JSON、HTML、XLSX 三种输出格式。
- 提供 `/docs` 交互式 OpenAPI 文档。

## 快速开始

### 本地运行

建议使用 Python 3.9 及以上版本；Python 3.12 与 Docker 镜像保持一致。

```shell
git clone https://github.com/neozhu/PaddleOCRFastAPI.git
cd PaddleOCRFastAPI

python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows PowerShell
# .\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

访问 <http://localhost:8000/docs> 即可调用接口。PaddleOCR 模型会在首次调用相关接口时下载，因此第一次请求通常比后续请求耗时更长。

### Docker Compose 运行

```shell
git clone https://github.com/neozhu/PaddleOCRFastAPI.git
cd PaddleOCRFastAPI
docker compose up --build -d
docker compose logs -f
```

Compose 默认暴露 `8000` 端口，并通过 `paddleocr_models` Docker 卷持久化 PaddleX 下载的模型。

## API 示例

以下示例默认服务地址为 `http://localhost:8000`。

### 上传图片 OCR

`POST /ocr/predict-by-file` 通过 multipart 表单字段 `file` 接收 `jpg`、`jpeg`、`png`、`bmp`、`tiff` 图片。

```shell
curl -X POST "http://localhost:8000/ocr/predict-by-file" \
  -F "file=@./receipt.png"
```

返回结果包含识别文本和对应的边界框：

```json
{
  "resultcode": 200,
  "message": "receipt.png",
  "data": [
    {
      "input_path": "...",
      "rec_texts": ["示例文本"],
      "rec_boxes": [[12, 20, 180, 54]]
    }
  ]
}
```

### 识别公开图片 URL

`GET /ocr/predict-by-url` 使用查询参数 `imageUrl`。

```shell
curl -G "http://localhost:8000/ocr/predict-by-url" \
  --data-urlencode "imageUrl=https://example.com/receipt.png"
```

其他图片 OCR 接口包括 `GET /ocr/predict-by-path`（参数 `image_path`）和 `POST /ocr/predict-by-base64`（请求体 `{"base64_str":"..."}`）。本地路径由服务端解析，只应传入运行服务的机器上可访问的文件。

### 识别图片或 PDF 中的第一个表格

`POST /table/predict-by-file` 通过 `file` 接收图片或 PDF。使用 `format` 选择 `json`（默认）、`html` 或 `xlsx` 输出。

```shell
curl -X POST "http://localhost:8000/table/predict-by-file?format=json" \
  -F "file=@./report.pdf"
```

当 `format=json` 时，响应同时包含生成的表格 HTML 和简化后的行数据：

```json
{
  "resultcode": 200,
  "message": "Success",
  "data": {
    "html": "<table>...</table>",
    "rows": [["表头 A", "表头 B"], ["值 1", "值 2"]]
  }
}
```

`GET /table/predict-by-url` 提供相同能力，使用公开文件的 `url` 查询参数，支持图片与 PDF URL。

### 从 PDF 提取表格

`POST /pdf/predict-by-file` 通过 `file` 接收 PDF，只返回检测到表格的页面。

```shell
curl -X POST "http://localhost:8000/pdf/predict-by-file" \
  -F "file=@./report.pdf"
```

如需处理公开 PDF，使用 `GET /pdf/predict-by-url`，查询参数为 `pdf_url`。

## 接口说明

| 接口 | 说明 |
| --- | --- |
| `GET /ocr/predict-by-path` | 识别服务端可访问的图片路径。 |
| `POST /ocr/predict-by-base64` | 识别 Base64 图片数据。 |
| `POST /ocr/predict-by-file` | 识别上传图片。 |
| `GET /ocr/predict-by-url` | 识别公开图片 URL。 |
| `POST /table/predict-by-file` | 识别上传图片或 PDF 中的第一个表格。 |
| `GET /table/predict-by-url` | 识别公开图片或 PDF URL 中的第一个表格。 |
| `POST /pdf/predict-by-file` | 从上传 PDF 中提取表格。 |
| `GET /pdf/predict-by-url` | 从公开 PDF URL 中提取表格。 |

## 常见说明

- 表格识别依赖与 PaddleOCR 匹配的 `paddlex[ocr]==3.7.1`，该依赖已包含在 `requirements.txt` 中。
- URL 接口要求服务端能够下载目标文件；请使用无需登录即可访问的链接。
- 当前仓库采用 CPU 兼容的默认配置，未包含 GPU 部署配置。

## 许可证

PaddleOCRFastAPI 使用 [MIT License](./LICENSE) 发布。
