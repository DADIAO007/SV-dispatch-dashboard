# SV派单数据看板

静态数据看板，所有数据预先生成并嵌入HTML，单文件部署到GitHub Pages。

## 本地开发

1. 启动HTTP服务器：`python3 -m http.server 8000`
2. 打开 http://127.0.0.1:8000/dashboard.html
3. 密码：`SV2026`

## 重新生成数据

```bash
python3 gen_data_v4.py  # 从 sv_dispatch.db 生成 dashboard_data.json
python3 gen_v4.py       # 生成 dashboard.html
cp dashboard.html output/index.html
```

## 部署

推送到main分支自动部署到GitHub Pages。
