
# 1. 文件下载服务器（file_download）

一个基于 Flask 的内网文件浏览与下载服务器，支持目录浏览、文件下载、API 获取文件列表（纯文本CSV格式），可通过 Docker 部署，支持 systemd 服务管理。

---


## 1.1 功能特性

- 支持通过网页浏览目录、下载文件，界面美观，支持面包屑导航
- 支持通过 API 获取指定目录下的文件/文件夹列表，返回纯文本 CSV 格式，便于脚本或自动化处理
- 支持大文件下载，安全路径校验，防止目录遍历攻击
- 支持 Docker 一键部署
- 支持 systemd 服务管理

---


## 2. 快速开始


### 2.1 安装依赖

```shell
pip install -r requirements.txt
```


### 2.2 启动服务

```shell
python3 web.py
# 默认监听 8080 端口
# 启动后访问 http://localhost:8080
```


### 2.3 目录结构

```
├── web.py                # 主程序入口
├── requirements.txt      # Python依赖
├── interface/            # 目录/文件信息处理模块
├── templates/main.html   # 网页模板
├── downloads/            # 默认文件存储目录
├── dependencies/         # Docker相关及证书
├── logs/                 # 日志目录
```

---


## 3. API 说明


### 3.1 获取文件/目录列表

```
GET /api/getfilelist?file_path=相对路径
```

**返回内容为纯文本CSV格式，每行一个条目，无表头：**

```
file,文件名,下载URL
folder,文件夹名,none
```

示例：

```
file,readme.txt,http://localhost:8080/download/readme.txt
folder,subfolder,none
```

> 可直接用 wget 批量下载：
> wget -O 文件名 "下载URL"

---


## 4. 网页端功能

- 支持目录树浏览、文件夹跳转、文件下载
- 文件类型、大小、修改时间一目了然
- 支持面包屑导航、上级目录跳转

---


## 5. Docker 部署


### 5.1 构建镜像

```shell
docker build -f dependencies/Dockerfile -t filedownload:v1 .
```


### 5.2 运行容器

```shell
docker run -d \
  -p 8888:8080 \
  -v /your/local/dir:/flask/downloads \
  --name filedownload \
  filedownload:latest
```

---


## 6. systemd 服务部署

1. 复制 service 文件到 systemd 目录
  ```shell
  sudo cp dependencies/file_download.service /etc/systemd/system/
  ```
2. 重新加载 systemd 配置
  ```shell
  sudo systemctl daemon-reload
  ```
3. 启用并启动服务
  ```shell
  sudo systemctl enable file_download.service
  sudo systemctl start file_download.service
  ```
4. 查看服务状态/日志
  ```shell
  sudo systemctl status file_download.service
  sudo journalctl -u file_download.service -f
  ```

---


## 7. 证书与私有源支持

如需对接私有源（如 nexus），可参考如下生成证书并在 Dockerfile 中添加：

```shell
openssl s_client -connect nexus.infra.timecho.com:8443 -showcerts </dev/null 2>/dev/null | openssl x509 -outform PEM > nexus-cert.pem
cp nexus-cert.pem dependencies/
```

---


## 8. 依赖导出与安装

```shell
pip freeze > requirements.txt
pip install -r requirements.txt
```

---


## 9. 常见问题

- 默认下载目录可在 web.py 里通过 DOWNLOAD_FOLDER 配置
- API 返回为纯文本，便于脚本处理
- 支持大文件、中文文件名

---


## 10. 联系与贡献

如有建议或问题，欢迎 issue 或 PR。