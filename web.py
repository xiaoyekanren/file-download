# coding=utf-8
"""
文件下载服务器 - 纯标准库实现，无需安装任何第三方模块
"""
import logging
import os
import urllib.parse
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from socketserver import ThreadingMixIn
from string import Template


# ==================== 配置 ====================

DOWNLOAD_FOLDER = os.environ.get('DOWNLOAD_FOLDER', os.path.dirname(os.path.abspath(__file__)))
PORT = 8080

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


# ==================== 工具函数 ====================

def get_file_size(file_path):
    """获取文件大小并格式化"""
    size = os.path.getsize(file_path)
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"


def get_file_info(file_path):
    """获取文件详细信息"""
    stat = os.stat(file_path)
    return {
        'name': os.path.basename(file_path),
        'size': get_file_size(file_path),
        'mtime': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
        'extension': Path(file_path).suffix[1:].upper() if Path(file_path).suffix else '-'
    }


def get_folder_info(folder_path):
    """获取文件夹信息"""
    stat = os.stat(folder_path)
    try:
        file_count = sum(1 for _ in os.scandir(folder_path) if _.is_file())
    except:
        file_count = 0
    return {
        'mtime': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
        'file_count': file_count
    }


def safe_join(base, path):
    """安全连接路径，防止目录遍历攻击"""
    base = os.path.abspath(base)
    target = os.path.abspath(os.path.join(base, path))
    if os.path.commonpath([base, target]) != base:
        return base
    return target


def list_directory(directory_path, base_path):
    """列出目录内容"""
    folders = []
    files = []

    try:
        for item in os.listdir(directory_path):
            item_path = os.path.join(directory_path, item)
            relative_path = os.path.relpath(item_path, base_path).replace(os.sep, '/')

            if os.path.isfile(item_path):
                info = get_file_info(item_path)
                info['relative_path'] = relative_path
                files.append(info)
            elif os.path.isdir(item_path):
                info = get_folder_info(item_path)
                info['name'] = item
                info['relative_path'] = relative_path
                info['url'] = '/' + urllib.parse.quote(relative_path)
                folders.append(info)
    except PermissionError:
        logging.warning(f"无权限访问: {directory_path}")
    except Exception as e:
        logging.error(f"读取目录错误: {directory_path} - {e}")

    folders.sort(key=lambda x: x['name'].lower())
    files.sort(key=lambda x: os.path.getmtime(os.path.join(directory_path, x['name'])), reverse=True)
    return folders, files


def get_breadcrumbs(current_path, base_path):
    """生成面包屑导航"""
    breadcrumbs = [{'name': '根目录', 'url': '/'}]

    if current_path == base_path:
        return breadcrumbs

    rel_path = os.path.relpath(current_path, base_path)
    if rel_path == '.':
        return breadcrumbs

    parts = rel_path.split(os.sep)
    current_url = ""
    for part in parts:
        current_url = os.path.join(current_url, part).replace(os.sep, '/')
        breadcrumbs.append({
            'name': part,
            'url': '/' + urllib.parse.quote(current_url)
        })
    return breadcrumbs


# ==================== HTML 模板 ====================

CSS = '''
* { box-sizing: border-box; margin: 0; padding: 0; }
:root {
    --primary: #3b82f6;
    --primary-hover: #2563eb;
    --primary-light: #eff6ff;
    --bg: #f8fafc;
    --surface: #ffffff;
    --border: #e2e8f0;
    --text: #0f172a;
    --text-secondary: #64748b;
    --text-muted: #94a3b8;
    --success: #10b981;
    --radius: 8px;
}
.dark {
    --bg: #0f172a;
    --surface: #1e293b;
    --border: #334155;
    --text: #f1f5f9;
    --text-secondary: #94a3b8;
    --text-muted: #64748b;
    --primary-light: #1e3a5f;
}
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
    font-size: 13px;
    line-height: 1.4;
    transition: background 0.3s, color 0.3s;
}
.container { max-width: 1000px; margin: 0 auto; padding: 12px; }

/* Header */
.header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
}
.logo { display: flex; align-items: center; gap: 8px; }
.logo-icon {
    width: 32px; height: 32px;
    background: linear-gradient(135deg, var(--primary), #8b5cf6);
    border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    color: white; font-size: 16px;
}
.logo h1 { font-size: 16px; font-weight: 700; }
.logo span { font-size: 11px; color: var(--text-muted); }
.header-right { display: flex; align-items: center; gap: 8px; }
.meta {
    display: flex; align-items: center; gap: 4px;
    padding: 5px 10px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 14px;
    font-size: 12px;
    color: var(--text-secondary);
}
.theme-btn {
    width: 32px; height: 32px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    cursor: pointer;
    font-size: 16px;
    display: flex; align-items: center; justify-content: center;
    transition: all 0.2s;
}
.theme-btn:hover { background: var(--border); }

/* Breadcrumb */
.breadcrumb-nav {
    display: flex; align-items: center; justify-content: space-between;
    padding: 8px 12px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    margin-bottom: 10px;
}
.breadcrumb { display: flex; align-items: center; gap: 2px; flex-wrap: wrap; }
.breadcrumb a {
    color: var(--primary);
    text-decoration: none;
    font-size: 13px;
    padding: 2px 6px;
    border-radius: 4px;
    transition: background 0.2s;
}
.breadcrumb a:hover { background: var(--primary-light); }
.breadcrumb .sep { color: var(--text-muted); margin: 0 2px; }
.breadcrumb .current { color: var(--text); font-weight: 500; padding: 2px 6px; }

/* API Button */
.api-btn {
    display: inline-flex; align-items: center; gap: 4px;
    padding: 4px 10px;
    background: var(--bg);
    color: var(--text-secondary);
    border: 1px solid var(--border);
    border-radius: 4px;
    text-decoration: none;
    font-size: 12px;
    transition: all 0.2s;
}
.api-btn:hover {
    background: var(--primary);
    color: white;
    border-color: var(--primary);
}

/* Stats */
.stats {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
    margin-bottom: 10px;
}
.stat-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 10px 12px;
    display: flex; align-items: center; gap: 10px;
}
.stat-icon {
    width: 28px; height: 28px;
    border-radius: 6px;
    display: flex; align-items: center; justify-content: center;
    font-size: 14px;
}
.stat-icon.total { background: #f3e8ff; color: #9333ea; }
.stat-icon.folder { background: #fef3c7; color: #d97706; }
.stat-icon.file { background: #dbeafe; color: #2563eb; }
.stat-value { font-size: 16px; font-weight: 700; }
.stat-label { font-size: 11px; color: var(--text-muted); }

/* Table */
.content-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    overflow: hidden;
}
table { width: 100%; border-collapse: collapse; }
th {
    text-align: left;
    padding: 8px 12px;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--text-muted);
    background: var(--bg);
    border-bottom: 1px solid var(--border);
}
td {
    padding: 8px 12px;
    border-bottom: 1px solid var(--border);
    vertical-align: middle;
}
tr:last-child td { border-bottom: none; }
tr:not(.parent-row):hover { background: var(--bg); }
tr.parent-row { background: var(--primary-light); }

.item-name { display: flex; align-items: center; gap: 8px; }
.item-icon {
    width: 26px; height: 26px;
    border-radius: 6px;
    display: flex; align-items: center; justify-content: center;
    font-size: 12px;
}
.item-icon.folder { background: linear-gradient(135deg, #fbbf24, #f59e0b); color: white; }
.item-icon.file { background: linear-gradient(135deg, #60a5fa, #3b82f6); color: white; }
.item-icon.parent { background: var(--border); color: var(--text-secondary); }
.item-name a {
    color: var(--text);
    text-decoration: none;
    font-weight: 500;
}
.item-name a:hover { color: var(--primary); }
.item-info { color: var(--text-secondary); font-size: 12px; }
.time-cell { color: var(--text-secondary); font-size: 12px; }

/* Action Button */
.btn {
    display: inline-flex; align-items: center; justify-content: center;
    width: 26px; height: 26px;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 4px;
    cursor: pointer;
    color: var(--text-secondary);
    font-size: 12px;
    transition: all 0.2s;
}
.btn:hover { background: var(--border); color: var(--text); }
.btn.copied { background: var(--success); border-color: var(--success); color: white; }

/* Empty State */
.empty {
    text-align: center;
    padding: 40px 16px;
    color: var(--text-muted);
}
.empty-icon { font-size: 40px; margin-bottom: 12px; }
.empty h3 { font-size: 14px; color: var(--text); margin-bottom: 4px; }

/* Toast */
.toast {
    position: fixed;
    bottom: 16px;
    left: 50%;
    transform: translateX(-50%) translateY(60px);
    background: var(--text);
    color: var(--bg);
    padding: 8px 16px;
    border-radius: 6px;
    font-size: 12px;
    opacity: 0;
    transition: all 0.3s;
    z-index: 1000;
}
.toast.show { transform: translateX(-50%) translateY(0); opacity: 1; }

/* Responsive */
@media (max-width: 600px) {
    .container { padding: 8px; }
    .header { flex-direction: column; align-items: flex-start; gap: 8px; }
    .stats { grid-template-columns: repeat(3, 1fr); gap: 6px; }
    th, td { padding: 6px 8px; }
    th:nth-child(2), td:nth-child(2) { display: none; }
    .breadcrumb-nav { flex-direction: column; align-items: flex-start; gap: 8px; }
}
'''

HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>文件下载服务器</title>
    <style>''' + CSS + '''</style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">
                <div class="logo-icon">📁</div>
                <div>
                    <h1>文件下载服务器</h1>
                    <span>File Download Server</span>
                </div>
            </div>
            <div class="header-right">
                <div class="meta">🕐 $current_time</div>
                <button class="theme-btn" onclick="toggleTheme()" title="切换主题">🌙</button>
            </div>
        </div>

        <nav class="breadcrumb-nav">
            <div class="breadcrumb">🏠 $breadcrumbs</div>
            <a href="/api/getfilelist?file_path=$current_path" class="api-btn" target="_blank">当前页API</a>
        </nav>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-icon total">📊</div>
                <div>
                    <div class="stat-value">$total_count</div>
                    <div class="stat-label">总项目</div>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-icon folder">📁</div>
                <div>
                    <div class="stat-value">$folders_count</div>
                    <div class="stat-label">文件夹</div>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-icon file">📄</div>
                <div>
                    <div class="stat-value">$files_count</div>
                    <div class="stat-label">文件</div>
                </div>
            </div>
        </div>

        $content

        <div class="toast" id="toast">已复制到剪贴板</div>
    </div>

    <script>
    // 主题切换
    function toggleTheme() {
        var body = document.body;
        var btn = document.querySelector('.theme-btn');
        body.classList.toggle('dark');
        var isDark = body.classList.contains('dark');
        btn.innerHTML = isDark ? '☀️' : '🌙';
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
    }
    (function() {
        var theme = localStorage.getItem('theme');
        if (theme === 'dark') {
            document.body.classList.add('dark');
            document.querySelector('.theme-btn').innerHTML = '☀️';
        }
    })();

    // 复制链接
    function copyLink(btn, url) {
        navigator.clipboard.writeText(url).then(function() {
            btn.classList.add('copied');
            btn.innerHTML = '✓';
            document.getElementById('toast').classList.add('show');
            setTimeout(function() {
                btn.classList.remove('copied');
                btn.innerHTML = '📋';
                document.getElementById('toast').classList.remove('show');
            }, 2000);
        });
    }
    </script>
</body>
</html>
'''

TABLE_TEMPLATE = '''
<div class="content-card">
    <table>
        <thead>
            <tr>
                <th>名称</th>
                <th>类型</th>
                <th style="width:90px">大小</th>
                <th style="width:140px">修改时间</th>
                <th style="width:50px"></th>
            </tr>
        </thead>
        <tbody>
            $rows
        </tbody>
    </table>
</div>
'''

EMPTY_TEMPLATE = '''
<div class="content-card">
    <div class="empty">
        <div class="empty-icon">📭</div>
        <h3>此目录为空</h3>
        <p>当前目录下没有文件或文件夹</p>
    </div>
</div>
'''


# ==================== HTTP Handler ====================

class FileHandler(BaseHTTPRequestHandler):
    """HTTP请求处理器"""

    def log_message(self, format, *args):
        """自定义日志格式"""
        logging.info("%s - %s", self.client_address[0], format % args)

    def send_html(self, html, status=200):
        """发送HTML响应"""
        data = html.encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', len(data))
        self.end_headers()
        self.wfile.write(data)

    def send_file(self, file_path):
        """发送文件下载"""
        try:
            file_size = os.path.getsize(file_path)
            file_name = os.path.basename(file_path)
            # 同时提供 ASCII filename 和 UTF-8 filename* 以兼容不同浏览器
            ascii_name = file_name.encode('ascii', 'replace').decode('ascii')
            self.send_response(200)
            self.send_header('Content-Type', 'application/octet-stream')
            self.send_header('Content-Length', file_size)
            self.send_header('Content-Disposition', f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{urllib.parse.quote(file_name)}")
            self.end_headers()

            with open(file_path, 'rb') as f:
                while chunk := f.read(65536):
                    self.wfile.write(chunk)

            logging.info(f"下载: {file_name} - {self.client_address[0]}")
        except Exception as e:
            logging.error(f"文件发送错误: {e}")
            self.send_error(500, str(e))

    def do_GET(self):
        """处理GET请求"""
        # 解析路径
        parsed = urllib.parse.urlparse(self.path)
        path = urllib.parse.unquote(parsed.path)

        # API: 获取文件列表
        if path == '/api/getfilelist':
            self.handle_api_list(parsed.query)
            return

        # 下载文件
        if path.startswith('/download/'):
            file_path = safe_join(DOWNLOAD_FOLDER, path[10:])  # 去掉 '/download/'
            logging.info(f"Download request: {path[10:]} -> {file_path}")
            if os.path.isfile(file_path):
                self.send_file(file_path)
                return
            self.send_error(404, 'File not found')
            return

        # 浏览目录
        if path == '/':
            current_dir = DOWNLOAD_FOLDER
        else:
            current_dir = safe_join(DOWNLOAD_FOLDER, path.lstrip('/'))

        if not os.path.exists(current_dir):
            self.send_error(404, 'Directory not found')
            return

        if os.path.isfile(current_dir):
            self.send_file(current_dir)
            return

        # 生成目录页面
        self.render_directory(current_dir)

    def handle_api_list(self, query):
        """API: 返回文件列表"""
        params = urllib.parse.parse_qs(query)
        file_path = params.get('file_path', [''])[0]

        if file_path:
            target_dir = safe_join(DOWNLOAD_FOLDER, file_path)
        else:
            target_dir = DOWNLOAD_FOLDER

        if not os.path.isdir(target_dir):
            self.send_error(404, 'Directory not found')
            return

        lines = []
        try:
            for item in os.listdir(target_dir):
                item_path = os.path.join(target_dir, item)
                rel_path = os.path.relpath(item_path, DOWNLOAD_FOLDER).replace(os.sep, '/')

                if os.path.isfile(item_path):
                    url = f"http://{self.headers.get('Host', 'localhost:8080')}/download/{urllib.parse.quote(rel_path)}"
                    lines.append(f"file,{item},{url}")
                elif os.path.isdir(item_path):
                    lines.append(f"folder,{item},none")
        except Exception as e:
            self.send_error(500, str(e))
            return

        data = '\n'.join(lines).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain; charset=utf-8')
        self.send_header('Content-Length', len(data))
        self.end_headers()
        self.wfile.write(data)

    def render_directory(self, current_dir):
        """渲染目录页面"""
        folders, files = list_directory(current_dir, DOWNLOAD_FOLDER)
        breadcrumbs = get_breadcrumbs(current_dir, DOWNLOAD_FOLDER)

        # 计算当前路径（相对路径）
        if current_dir == DOWNLOAD_FOLDER:
            current_path = ''
        else:
            current_path = os.path.relpath(current_dir, DOWNLOAD_FOLDER).replace(os.sep, '/')

        # 计算上级目录
        if current_dir != DOWNLOAD_FOLDER:
            parent = os.path.dirname(current_dir)
            parent_rel = os.path.relpath(parent, DOWNLOAD_FOLDER)
            parent_url = '/' if parent_rel == '.' else '/' + urllib.parse.quote(parent_rel.replace(os.sep, '/'))
        else:
            parent_url = None

        # 生成面包屑HTML
        breadcrumb_html = ''
        for i, crumb in enumerate(breadcrumbs):
            if i < len(breadcrumbs) - 1:
                breadcrumb_html += f'<a href="{crumb["url"]}">{crumb["name"]}</a><span class="sep">/</span>'
            else:
                breadcrumb_html += f'<span class="current">{crumb["name"]}</span>'

        # 生成表格行
        rows = ''

        # 返回上级
        if parent_url:
            rows += f'''<tr class="parent-row">
                <td><div class="item-name"><div class="item-icon parent">⬅</div><a href="{parent_url}">返回上级</a></div></td>
                <td class="item-info">-</td>
                <td class="item-info">-</td>
                <td class="time-cell">-</td>
                <td></td>
            </tr>'''

        # 文件夹
        for f in folders:
            rows += f'''<tr>
                <td><div class="item-name"><div class="item-icon folder">📁</div><a href="{f["url"]}">{f["name"]}</a></div></td>
                <td class="item-info">文件夹</td>
                <td class="item-info">{f["file_count"]}项</td>
                <td class="time-cell">{f["mtime"]}</td>
                <td></td>
            </tr>'''

        # 文件
        base_url = f"http://{self.headers.get('Host', 'localhost:8080')}"
        for f in files:
            download_url = f"{base_url}/download/{urllib.parse.quote(f['relative_path'])}"
            rows += f'''<tr>
                <td><div class="item-name"><div class="item-icon file">📄</div><a href="/download/{urllib.parse.quote(f["relative_path"])}">{f["name"]}</a></div></td>
                <td class="item-info">{f["extension"]}</td>
                <td class="item-info">{f["size"]}</td>
                <td class="time-cell">{f["mtime"]}</td>
                <td><button class="btn" onclick="copyLink(this, \'{download_url}\')" title="复制链接">📋</button></td>
            </tr>'''

        # 内容区域
        if folders or files:
            content = Template(TABLE_TEMPLATE).substitute(rows=rows)
        else:
            content = EMPTY_TEMPLATE

        # 完整页面
        html = Template(HTML_TEMPLATE).substitute(
            current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            current_path=urllib.parse.quote(current_path),
            breadcrumbs=breadcrumb_html,
            total_count=len(folders) + len(files),
            folders_count=len(folders),
            files_count=len(files),
            content=content
        )

        self.send_html(html)


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """多线程HTTP服务器"""
    daemon_threads = True


# ==================== 启动 ====================

if __name__ == '__main__':
    print("=" * 50)
    print("文件下载服务器启动 (纯标准库版)")
    print(f"目录: {os.path.abspath(DOWNLOAD_FOLDER)}")
    print(f"地址: http://0.0.0.0:{PORT}")
    print("=" * 50)

    server = ThreadedHTTPServer(('0.0.0.0', PORT), FileHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务器已停止")
        server.shutdown()