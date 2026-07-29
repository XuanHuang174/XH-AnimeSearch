# AnimeSearch API 文档

## 概述

本服务提供动漫资源搜索与 Magnet 健康检查能力，供前端调用。

**基础 URL**: `https://animesearch.nalanyinyun.work`

**在线文档**: 服务启动后可访问 `/docs`（Swagger UI）或 `/redoc`（ReDoc）查看交互式文档。

---

## 接口列表

| 方法 | 路径 | 说明 |
| :--- | :--- | :--- |
| `GET` | `/` | 服务信息与可用接口说明 |
| `GET` | `/search` | 按关键词搜索 DMHY 动漫资源 |
| `GET` | `/health` | 检查 Magnet URI 健康状态（代理转发） |

---

## 1. 服务信息

**请求**:
- **方法**: `GET`
- **路径**: `/`

**成功响应 (200 OK)**:

```json
{
  "message": "Nalanyinyun DMHY Anime Search API",
  "version": "on development",
  "usage": [
    "GET /search?keyword=<keyword>&page=<page_number>",
    "GET /health?magnet=<magnet_link>"
  ],
  "comment": "More function will be added in the future"
}
```

---

## 2. 搜索动漫资源

从 [share.dmhy.org](https://share.dmhy.org) 抓取并结构化返回搜索结果。

**请求**:
- **方法**: `GET`
- **路径**: `/search`

**请求参数 (Query Params)**:

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| `keyword` | string | 是 | — | 搜索关键词，至少 1 个字符 |
| `page` | integer | 否 | `1` | 页码，从 1 开始 |

**成功响应 (200 OK)**:

返回 JSON 数组，每项为一条资源记录：

```json
[
  {
    "published_at": "2026-07-01 12:00",
    "category": "动画",
    "title": "[SubGroup] Anime Title - 01 [1080p]",
    "fansub": "SubGroup",
    "anime_title": "Anime Title",
    "url": "https://share.dmhy.org/topics/view/123456",
    "magnet": "magnet:?xt=urn:btih:...",
    "size": "500MB",
    "seeders": "10",
    "leechers": "2",
    "downloads": "100",
    "uploader": "username"
  }
]
```

**字段说明**:

| 字段 | 类型 | 说明 |
| :--- | :--- | :--- |
| `published_at` | string | 发布时间 |
| `category` | string | 分类（如「动画」） |
| `title` | string | 原始标题 |
| `fansub` | string \| null | 字幕组名称（从标题或标签解析） |
| `anime_title` | string \| null | 解析出的番剧名（去除集数、分辨率等后缀） |
| `url` | string | DMHY 详情页链接 |
| `magnet` | string \| null | Magnet 链接，部分条目可能为空 |
| `size` | string | 文件大小 |
| `seeders` | string | 做种数 |
| `leechers` | string | 下载数 |
| `downloads` | string | 完成数 |
| `uploader` | string | 发布者 |

**错误响应**:

- **422 Unprocessable Entity**: `keyword` 缺失或为空
  ```json
  {
    "detail": [
      {
        "loc": ["query", "keyword"],
        "msg": "String should have at least 1 character",
        "type": "string_too_short"
      }
    ]
  }
  ```

**前端调用示例**:

```typescript
async function searchAnime(keyword: string, page = 1) {
  const params = new URLSearchParams({ keyword, page: String(page) });
  const response = await fetch(
    `https://your-deployed-domain.vercel.app/search?${params}`
  );

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return response.json();
}

// 使用示例
const results = await searchAnime("葬送的芙莉莲", 1);
console.log(`共 ${results.length} 条结果`);
```

```bash
curl "https://your-deployed-domain.vercel.app/search?keyword=葬送的芙莉莲&page=1"
```

---

## 3. Magnet 健康检查

检查 Magnet URI 的健康状态，包括格式验证、DHT 节点发现、Peer 连接建立和元数据获取。

> **说明**: 本接口为代理接口。前端只需调用本服务的 `/health`，无需携带 `X-API-Key`；服务端会使用环境变量中的密钥转发至上游 Magnet 检查服务，并将响应原样返回。

**请求**:
- **方法**: `GET`
- **路径**: `/health`
- **超时**: 上游限制 15 秒（超时返回 408）

**请求参数 (Query Params)**:

| 参数名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| `magnet` | string | 是 | 完整的 Magnet URI（例如: `magnet:?xt=urn:btih:...`） |

**成功响应 (200 OK)**:

```json
{
  "valid": true,
  "dht": {
    "peer_count": 21
  },
  "connection": {
    "connected": 8
  },
  "metadata": {
    "elapsed_ms": 1432
  },
  "elapsed_ms": 1816
}
```

**部分失败响应 (200 OK)**:

*注：即使子项失败，只要总时长未超时，主状态码仍为 200。失败项返回 `false`。*

```json
{
  "valid": true,
  "dht": false,
  "connection": {
    "connected": 3
  },
  "metadata": false,
  "elapsed_ms": 5000
}
```

**字段说明**:

| 字段 | 类型 | 说明 |
| :--- | :--- | :--- |
| `valid` | boolean | Magnet 格式是否合法 |
| `dht` | object \| boolean | DHT 查询结果。成功时返回 `{ "peer_count": int }`，失败/超时返回 `false` |
| `connection` | object \| boolean | Peer 连接结果。成功时返回 `{ "connected": int }`，失败/超时返回 `false` |
| `metadata` | object \| boolean | 元数据获取结果。成功时返回 `{ "elapsed_ms": int }`，失败/超时返回 `false` |
| `elapsed_ms` | int | 整个请求消耗的总时间（毫秒） |

**错误响应**:

- **408 Request Timeout**: 检查超过 15 秒未完成
  ```json
  { "detail": "Request timed out after 15 seconds" }
  ```
- **422 Unprocessable Entity**: `magnet` 参数缺失或为空
  ```json
  {
    "detail": [
      {
        "loc": ["query", "magnet"],
        "msg": "String should have at least 1 character",
        "type": "string_too_short"
      }
    ]
  }
  ```

**前端调用示例**:

```typescript
async function checkMagnetHealth(magnetUri: string) {
  const params = new URLSearchParams({ magnet: magnetUri });
  const response = await fetch(
    `https://your-deployed-domain.vercel.app/health?${params}`,
    { method: "GET" }
  );

  if (response.status === 408) {
    throw new Error("请求超时：种子资源过于冷门或网络不通");
  }

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  const data = await response.json();

  if (!data.valid) {
    console.warn("Magnet 格式不正确");
    return data;
  }

  console.log(`总耗时: ${data.elapsed_ms}ms`);

  if (data.dht) {
    console.log(`发现 DHT 节点数: ${data.dht.peer_count}`);
  } else {
    console.log("DHT 查询失败");
  }

  if (data.connection) {
    console.log(`成功连接 Peer 数: ${data.connection.connected}`);
  } else {
    console.log("Peer 连接失败");
  }

  if (data.metadata) {
    console.log(`元数据获取耗时: ${data.metadata.elapsed_ms}ms`);
  } else {
    console.log("元数据获取失败");
  }

  return data;
}

// 使用示例
const magnet =
  "magnet:?xt=urn:btih:0eb308382b47ee044a2c33a4f9feb46732671706&dn=archlinux-2026.07.01-x86_64.iso";
checkMagnetHealth(magnet);
```

```bash
curl -X GET "https://your-deployed-domain.vercel.app/health?magnet=magnet:?xt=urn:btih:0eb308382b47ee044a2c33a4f9feb46732671706&dn=archlinux-2026.07.01-x86_64.iso"
```

---

## 注意事项

### 搜索接口 (`/search`)

1. **分页**: 每页结果数量由 DMHY 站点决定，通常约 40 条；无更多结果时返回空数组 `[]`。
2. **解析字段**: `fansub` 与 `anime_title` 由服务端从标题字符串启发式解析，部分复杂标题可能不准确。
3. **Magnet 链接**: 部分条目可能没有 Magnet 链接（`magnet` 为 `null`），前端需做空值判断。
4. **CORS**: 若前端为浏览器直连，需确保部署环境已配置 CORS（FastAPI 默认未开启跨域，Vercel 部署时需额外配置）。

### 健康检查接口 (`/health`)

1. **超时处理**: 上游硬限制为 15 秒。如果种子非常冷门（无做种者），可能会触发 408 超时，前端需做好 Loading 状态和超时提示。
2. **并发限制**: 虽然支持并发，但建议不要瞬间发起大量请求，以免触发上游限流或导致 libtorrent Session 负载过高。
3. **结果解读**:
   - `valid: true` 仅代表 Magnet 链接格式正确，不代表种子一定有资源。
   - `dht`、`connection`、`metadata` 均为 `false` 通常意味着该种子已死（无活跃 Peer）。
4. **鉴权**: 前端调用本服务时无需传递 API Key；密钥由服务端通过环境变量 `MAGNETCHECK_API_KEY` 注入并在代理请求时使用。
