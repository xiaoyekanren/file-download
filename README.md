# 文件下载服务器

一个简洁美观的内网文件浏览与下载服务器，**纯 Python 标准库实现，无需安装任何依赖**。

## 功能特性

- **零依赖** - 纯标准库实现，无需 pip install
- **现代化界面** - 简洁美观的 UI，支持暗色模式自动切换
- **目录浏览** - 面包屑导航，文件夹/文件分类展示
- **一键复制** - 文件下载链接一键复制到剪贴板
- **API 接口** - CSV 格式文件列表，便于脚本批量下载
- **安全可靠** - 路径校验防目录遍历，支持大文件下载
- **单文件部署** - 仅需 `web.py` 一个文件即可运行

## 快速开始

### 直接运行

```bash
# 默认使用当前目录作为下载目录
python web.py

# 指定下载目录
DOWNLOAD_FOLDER=/path/to/files python web.py
```

启动后访问 http://localhost:8080

### Docker 部署

```bash
# 构建镜像
docker build -t file-download .

# 运行容器（将 /path/to/files 替换为实际的文件目录）
docker run -d -p 8080:8080 -v /path/to/files:/data file-download
```

## 使用说明

### Web 界面

| 操作 | 说明 |
|------|------|
| 点击文件名 | 下载文件 |
| 点击「复制」按钮 | 复制下载链接到剪贴板 |
| 点击文件夹名 | 进入子目录 |
| 点击面包屑导航 | 快速返回上级目录 |
| 点击「当前页API」 | 获取当前目录的文件列表 API |

### API 接口

获取文件列表（CSV 格式）：

```
GET /api/getfilelist?file_path=相对路径
```

返回示例：
```
folder,documents,none
file,readme.txt,http://localhost:8080/download/readme.txt
file,report.pdf,http://localhost:8080/download/report.pdf
```

**批量下载脚本示例：**

```bash
# 获取文件列表并下载所有文件
curl -s "http://localhost:8080/api/getfilelist" | grep "^file," | while IFS=, read -r type name url; do
    wget -O "$name" "$url"
done
```

## 配置项

| 环境变量 | 说明 | 默认值 |
|---------|------|--------|
| `DOWNLOAD_FOLDER` | 文件下载目录 | 脚本所在目录 |
| `PORT` | 监听端口 | 8080 |

## 目录结构

```
file-download/
├── web.py           # 主程序（单文件即可运行）
├── start_server.sh  # 后台启动脚本
├── Dockerfile       # Docker 镜像构建文件
└── README.md        # 说明文档
```

## 界面预览

- 支持亮色/暗色模式（跟随系统）
- 响应式布局，适配移动端
- 文件类型图标区分
- 统计信息卡片展示

## License

MIT