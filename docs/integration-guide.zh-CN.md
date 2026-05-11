# 通用资产截图解析服务接入说明

本文面向其他项目接入 `asset-screenshot-parser-service`。服务负责 OCR、截图类型识别、持仓字段解析和案例/模板管理；消费方项目只需要上传截图并消费结构化结果。

## 1. 服务边界

本服务负责：

- 接收资产截图。
- 调用 OCR Provider，默认 `umi_http`。
- 将 OCR 结果标准化为 `ocr.lines`。
- 识别截图类型。
- 解析为 `snapshot_candidate.summary` 和 `snapshot_candidate.positions`。
- 保存解析快照、模板和测试案例，便于后续回归。

消费方项目负责：

- 用户认证、上传入口和业务权限。
- 图片来源管理，例如移动端上传、飞书消息、对象存储。
- 将解析结果展示给用户确认。
- 把确认后的持仓写入自己的业务库。
- 股票/基金代码补全、资产分类增强、价格提醒等业务逻辑。

本服务不负责：

- 登录券商、支付宝、同花顺等第三方账号。
- 交易、下单、调仓。
- 直接读取真实账户数据。
- 替消费方判断某条资产是否应被自动确认。

## 2. 环境变量约定

消费方建议使用以下配置项：

```env
ASSET_PARSER_BASE_URL=http://localhost:8010
ASSET_PARSER_API_KEY=
ASSET_PARSER_TIMEOUT_SECONDS=90
```

生产环境中 `ASSET_PARSER_BASE_URL` 应指向部署后的服务地址。不要在代码里写死域名、IP、API Key 或端口。

如果服务端设置了 `API_KEY`，消费方每次调用解析、模板和案例接口时必须带：

```http
X-API-Key: <asset-parser-api-key>
```

`GET /api/v1/health` 不需要鉴权。

## 3. 当前支持范围

| source_platform | screenshot_type | 场景 |
| --- | --- | --- |
| `ths_stock` | `ths_stock_positions_mobile_v1` | 同花顺移动端股票/ETF 持仓截图 |
| `alipay_fund` | `alipay_fund_positions_mobile_v1` | 支付宝移动端基金持仓截图 |

后续新增平台时，应优先新增枚举、parser、模板和案例，而不是让消费方直接解析 OCR 文本。

## 4. 最推荐调用方式

对大多数项目，推荐用 `POST /api/v1/screenshots/parse` 上传文件。

```bash
curl -X POST "$ASSET_PARSER_BASE_URL/api/v1/screenshots/parse" \
  -H "X-API-Key: $ASSET_PARSER_API_KEY" \
  -F "file=@./ths-stock.jpg" \
  -F "source_platform=ths_stock"
```

如果图片已经在消息队列、飞书回调或 JSON API 中，使用 `POST /api/v1/screenshots/parse-json`：

```bash
IMAGE_BASE64="$(base64 < ./alipay-fund.jpg | tr -d '\n')"

curl -X POST "$ASSET_PARSER_BASE_URL/api/v1/screenshots/parse-json" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $ASSET_PARSER_API_KEY" \
  -d "{
    \"image_base64\": \"$IMAGE_BASE64\",
    \"mime_type\": \"image/jpeg\",
    \"source_platform\": \"alipay_fund\"
  }"
```

## 5. 响应里应该消费哪些字段

消费方通常只需要使用：

```json
{
  "request_id": "8b160efd-23d7-4f8f-a17e-52c41fc5a12f",
  "ocr_provider": "umi_http",
  "screenshot_type": "ths_stock_positions_mobile_v1",
  "classification_confidence": "high",
  "warnings": [],
  "snapshot_candidate": {
    "summary": {
      "total_market_value": 34049.0,
      "total_profit": -8734.8,
      "position_count": 4,
      "currency": "CNY"
    },
    "positions": [
      {
        "asset_type": "stock",
        "source_platform": "ths_stock",
        "display_name": "航天发展",
        "symbol": null,
        "market": "cn",
        "quantity": 300.0,
        "market_value": 8376.0,
        "cost_price": 39.017,
        "profit_amount": -3338.19,
        "profit_pct": -28.44,
        "price": 27.92,
        "confidence": "high"
      }
    ]
  }
}
```

字段含义：

| 字段 | 含义 |
| --- | --- |
| `request_id` | 本次解析请求 ID，建议消费方落库，便于排查 |
| `ocr_provider` | 实际使用的 OCR 通道，例如 `umi_http` |
| `screenshot_type` | 服务识别出的截图类型 |
| `classification_confidence` | 截图分类置信度 |
| `warnings` | 可展示给用户或进入人工复核队列 |
| `summary.total_market_value` | 本次截图识别出的总市值/总金额 |
| `summary.total_profit` | 本次截图识别出的总盈亏/持有收益 |
| `positions[].display_name` | OCR 识别出的资产名称 |
| `positions[].symbol` | 当前可能为空，消费方可自行补全 |
| `positions[].quantity` | 持仓数量，基金截图通常为空 |
| `positions[].market_value` | 持仓市值或持有金额 |
| `positions[].cost_price` | 成本价，股票/ETF 截图中常见 |
| `positions[].price` | 当前价，股票/ETF 截图中常见 |
| `positions[].profit_amount` | 盈亏金额或持有收益 |
| `positions[].profit_pct` | 盈亏比例或持有收益率 |
| `positions[].confidence` | 当前行解析置信度 |

不建议消费方强依赖：

- `ocr.raw_result`：这是 OCR 原始返回，后续可能随 provider 变化。
- `raw_payload`：主要用于调试和案例回归。
- 未认识的新字段：应忽略，保持向后兼容。

## 6. Python 调用示例

```python
from __future__ import annotations

import os
from pathlib import Path

import requests


BASE_URL = os.environ["ASSET_PARSER_BASE_URL"].rstrip("/")
API_KEY = os.environ.get("ASSET_PARSER_API_KEY", "")


def parse_asset_screenshot(image_path: str, source_platform: str) -> dict:
    headers = {"X-API-Key": API_KEY} if API_KEY else {}
    with Path(image_path).open("rb") as file_obj:
        response = requests.post(
            f"{BASE_URL}/api/v1/screenshots/parse",
            headers=headers,
            files={"file": file_obj},
            data={"source_platform": source_platform},
            timeout=90,
        )
    response.raise_for_status()
    return response.json()


result = parse_asset_screenshot("./ths-stock.jpg", "ths_stock")
positions = result["snapshot_candidate"]["positions"]
for item in positions:
    print(item["display_name"], item["market_value"], item["profit_amount"])
```

## 7. TypeScript 调用示例

Node.js 18+ 可以直接使用内置 `fetch`、`FormData` 和 `Blob`。

```ts
import { readFile } from "node:fs/promises";

type SourcePlatform = "ths_stock" | "alipay_fund";

export async function parseAssetScreenshot(
  imagePath: string,
  sourcePlatform: SourcePlatform,
) {
  const baseUrl = process.env.ASSET_PARSER_BASE_URL;
  const apiKey = process.env.ASSET_PARSER_API_KEY;
  if (!baseUrl) {
    throw new Error("ASSET_PARSER_BASE_URL is required");
  }

  const image = await readFile(imagePath);
  const form = new FormData();
  form.append("file", new Blob([image], { type: "image/jpeg" }), "screenshot.jpg");
  form.append("source_platform", sourcePlatform);

  const response = await fetch(`${baseUrl.replace(/\/$/, "")}/api/v1/screenshots/parse`, {
    method: "POST",
    headers: apiKey ? { "X-API-Key": apiKey } : undefined,
    body: form,
  });

  if (!response.ok) {
    throw new Error(`Asset parser failed: ${response.status} ${await response.text()}`);
  }
  return response.json();
}
```

## 8. 消费方推荐业务流程

1. 用户上传截图，或飞书/移动端把截图转发给消费方项目。
2. 消费方把原图保存到自己的临时存储或对象存储。
3. 消费方调用 asset parser 服务。
4. 消费方展示 `snapshot_candidate.positions` 给用户确认。
5. 用户确认后，消费方写入自己的持仓表、自选表或资产快照表。
6. 如果 `warnings` 非空或 `confidence=low`，进入人工复核。
7. 消费方按自己的业务规则做代码补全、价格提醒、估值计算、飞书/邮件推送。

## 9. 错误处理建议

| 状态码 | 场景 | 消费方动作 |
| --- | --- | --- |
| `401` | API Key 缺失或错误 | 不重试，提示配置错误 |
| `422` | 参数不合法，例如平台枚举错误 | 不重试，修正请求 |
| `500` | OCR、图片解码或 parser 失败 | 可有限重试，并进入人工复核 |

建议：

- OCR 调用超时建议设置为 `60-90s`。
- 不要无限重试，避免 OCR 服务被压垮。
- 保存 `request_id`、原图 URI、source_platform、错误信息，便于复盘。
- 对钱相关数据，默认让用户确认后再覆盖正式持仓。

## 10. 与 daily_stock_analysis 的接入建议

`daily_stock_analysis` 应把本服务当作外部解析能力：

- Web 上传截图后调用 `/api/v1/screenshots/parse`。
- 拿到 `snapshot_candidate` 后进入“待确认持仓快照”。
- 用户确认后再写入 external holdings 数据表或飞书文档。
- 不要把 Umi-OCR HTTP 调用、OCR 行过滤、截图布局 parser 复制回 `daily_stock_analysis`。

推荐最小配置：

```env
EXTERNAL_HOLDINGS_ENABLED=true
ASSET_PARSER_BASE_URL=<asset-parser-service-url>
ASSET_PARSER_API_KEY=<asset-parser-api-key>
ASSET_PARSER_TIMEOUT_SECONDS=90
```

## 11. 模板和案例接口怎么用

模板用于记录某类截图的布局/解析规则：

```bash
curl -X POST "$ASSET_PARSER_BASE_URL/api/v1/templates" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $ASSET_PARSER_API_KEY" \
  -d '{
    "template_id": "alipay_fund_positions_mobile_v1:default",
    "screenshot_type": "alipay_fund_positions_mobile_v1",
    "source_platform": "alipay_fund",
    "layout_version": "v1",
    "status": "active",
    "notes": "Default Alipay fund mobile holding parser"
  }'
```

案例用于沉淀真实截图回归样例：

```bash
curl -X POST "$ASSET_PARSER_BASE_URL/api/v1/cases" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $ASSET_PARSER_API_KEY" \
  -d '{
    "case_id": "alipay-fund-mobile-001",
    "screenshot_type": "alipay_fund_positions_mobile_v1",
    "source_platform": "alipay_fund",
    "template_id": "alipay_fund_positions_mobile_v1:default",
    "image_uri": "s3://asset-parser-cases/alipay-fund-mobile-001.jpg",
    "expected_snapshot": {},
    "actual_snapshot": {},
    "status": "verified"
  }'
```

推荐把失败截图也登记为 `failed` 案例，修复 parser 后再更新为 `verified`，这样后续新增截图类型时不会破坏已支持的手机截图。

## 12. 接入验收清单

- `GET /api/v1/health` 可访问。
- 消费方已配置 `ASSET_PARSER_BASE_URL`。
- 如果服务端启用了 `API_KEY`，消费方已配置 `ASSET_PARSER_API_KEY`。
- 至少用一张同花顺截图和一张支付宝截图跑通。
- 消费方落库的是用户确认后的 `snapshot_candidate`，不是未经确认的 OCR 文本。
- 失败请求有日志，日志里包含 `request_id` 或消费方自己的 upload id。
- 图片和响应数据按消费方隐私策略保存或清理。
