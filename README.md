# AnimeSearch API Source

这是 AnimeSearch API 的源代码，此 API 提供从 DMHY 查询资源，以及检查 Magnet 可用性两种功能。

## 用法

见 `API_DOCUMENTATION.md`

## 可用性

没有任何 SLA，除了愿意花钱的人和这个项目的贡献者。

实际 SLA 取决于 Vercel Hobby 计划限额，超额会导致所有人都无法使用。

## 关于 GET /

从这个接口获取到的任何信息都没有作用。

版本号不会更新，因为没有用。这个 API 采用滚动发行模式，更改会被直接部署至**生产环境**，如果你需要兼容性保证，可用性保证，请自行部署。

## API 鉴权

目前没有鉴权，接口是公开的。如果发现滥用或使用量过大，会添加鉴权。

公开的接口中，GET /health 是另一个 API 的代理（这个 API 非常贵，望周知），源代码见 `MagnetCheck`，直接调用上游接口会返回 402。

## 如何定义滥用？

凭感觉。

## 部署

```bash
uv run main.py
```

自行部署请将 /health 接口的上游替换为你的自定义实现，`magnetcheck` 不是公共 API.

