#



## linux - service

``` shell
# 1. 将 service 文件复制到 systemd 目录
sudo cp ~/clamav-mirror/clamav-mirror.service /etc/systemd/system/

# 2. 重新加载 systemd 配置
sudo systemctl daemon-reload

# 3. 启用开机自启
sudo systemctl enable clamav-mirror.service

# 4. 立即启动服务
sudo systemctl start clamav-mirror.service

# 5. 查看服务状态
sudo systemctl status clamav-mirror.service

# 6. 查看日志
sudo journalctl -u clamav-mirror.service -f
```


## python
导出依赖
``` shell
pip freeze >> requirements.txt
pip install -r requirements.txt
``` 

## docker

``` shell
# 构建镜像
docker build -f dependencies/Dockerfile -t timecho/filedownload:v1 .
 
# 启动镜像
docker run -d \
  -p 8888:8080 \
  -v /home/zzm:/flask/downloads \
  --name timecho/filedownload \
  timecho/filedownload:v0.1

``` 

## 给nexus生成证书
``` shell
openssl s_client -connect nexus.infra.timecho.com:8443 -showcerts </dev/null 2>/dev/null | openssl x509 -outform PEM > nexus-cert.pem


COPY nexus-cert.pem /usr/local/share/ca-certificates/nexus-infra-timecho-com.crt

```