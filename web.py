# coding=utf-8
from flask import Flask, send_from_directory, render_template, request, jsonify, Response
import os
import logging
from datetime import datetime
import urllib.parse
from interface import *
from pathlib import Path
import csv
from io import StringIO


app = Flask(__name__)

# 配置
DOWNLOAD_FOLDER = '/Users/zzm/Downloads'
# 创建下载目录
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


@app.route('/')
@app.route('/<path:subpath>')
def index(subpath=""):
    """显示目录内容"""
    # 构建请求的完整路径
    if subpath:
        # 安全处理路径，防止目录遍历攻击
        safe_subpath = safe_join(DOWNLOAD_FOLDER, subpath)
        current_dir = safe_subpath
    else:
        current_dir = DOWNLOAD_FOLDER

    # 检查路径是否存在
    if not os.path.exists(current_dir):
        return "目录不存在", 404

    # 如果是文件，直接提供下载
    if os.path.isfile(current_dir):
        return download_file(subpath)

    # 列出目录内容
    folders, files = list_directory(current_dir, DOWNLOAD_FOLDER)

    # 计算统计信息
    items_count = len(folders) + len(files)
    folders_count = len(folders)
    files_count = len(files)

    # 生成面包屑导航
    breadcrumbs = get_breadcrumbs(current_dir, DOWNLOAD_FOLDER)

    # 计算当前目录相对于基路径的显示路径
    if current_dir == DOWNLOAD_FOLDER:
        current_dir_display = '/'
    else:
        current_dir_display = '/' + os.path.relpath(current_dir, DOWNLOAD_FOLDER).replace(os.sep, '/')

    # 生成上级目录链接
    if current_dir != DOWNLOAD_FOLDER:
        parent_dir = os.path.dirname(current_dir)
        parent_relative = os.path.relpath(parent_dir, DOWNLOAD_FOLDER)
        if parent_relative == '.':
            parent_url = '/'
        else:
            parent_url = '/' + urllib.parse.quote(parent_relative.replace(os.sep, '/'))
    else:
        parent_url = None

    return render_template('main.html',
                           folders=folders,
                           files=files,
                           items_count=items_count,
                           folders_count=folders_count,
                           files_count=files_count,
                           breadcrumbs=breadcrumbs,
                           current_dir=current_dir_display,
                           parent_url=parent_url,
                           current_path=os.path.abspath(DOWNLOAD_FOLDER),
                           current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))


def safe_join(base, path):
    """安全地连接路径，防止目录遍历攻击"""
    base = os.path.abspath(base)
    target = os.path.abspath(os.path.join(base, path))

    # 确保目标路径在基路径内
    if os.path.commonpath([base, target]) != base:
        return base  # 如果路径尝试逃逸，则返回基路径

    return target


@app.route('/api/getfilelist', methods=['GET'])
def api_getfilelist():
    """
    获取指定目录的文件列表（CSV格式显示在页面）
    参数: file_path - 相对于根目录的路径（可选）
    返回格式（每行一个条目）:
    - 文件: file, file_name, wget_url
    - 文件夹: folder, folder_name, none
    """
    try:
        # 获取 file_path 参数，默认为空
        file_path = request.args.get('file_path', '')
        
        # 构建完整路径
        if file_path:
            target_dir = safe_join(DOWNLOAD_FOLDER, file_path)
        else:
            target_dir = DOWNLOAD_FOLDER
        
        # 检查路径是否存在
        if not os.path.exists(target_dir):
            return "404", 404
        
        # 检查是否是文件而非目录
        if os.path.isfile(target_dir):
            return "400", 400
        
        # 列出目录内容
        items = []
        
        try:
            for item in os.listdir(target_dir):
                item_path = os.path.join(target_dir, item)
                relative_path = os.path.relpath(item_path, DOWNLOAD_FOLDER)
                
                if os.path.isfile(item_path):
                    # 构建 wget 下载 URL
                    url = 'http://localhost:8080/download/' + urllib.parse.quote(relative_path.replace(os.sep, '/'))
                    items.append({
                        'type': 'file',
                        'name': item,
                        'url': url
                    })
                elif os.path.isdir(item_path):
                    # 文件夹
                    items.append({
                        'type': 'folder',
                        'name': item,
                        'url': 'none'
                    })
        
        except PermissionError as e:
            logging.warning(f"没有权限访问目录: {target_dir} - {e}")
            return "403", 403
        except Exception as e:
            logging.error(f"读取目录错误: {target_dir} - {e}")
            return "500", 500
        
        # 排序：文件夹在前，文件在后，都按名称排序
        folders = [item for item in items if item['type'] == 'folder']
        files = [item for item in items if item['type'] == 'file']
        folders.sort(key=lambda x: x['name'].lower())
        files.sort(key=lambda x: x['name'].lower())
        items = folders + files
        
        # 生成 CSV 格式纯文本
        output = StringIO()
        writer = csv.writer(output)
        
        # 写入数据行
        for item in items:
            writer.writerow([
                item['type'],
                item['name'],
                item['url']
            ])
        
        logging.info(f"API获取文件列表: {file_path or '根目录'} - 共 {len(items)} 项")
        
        # 返回纯文本格式
        return Response(
            output.getvalue(),
            mimetype='text/plain; charset=utf-8'
        )
    
    except Exception as e:
        logging.error(f"API错误: {e}")
        return "500", 500


@app.route('/download/<path:filename>')
def download_file(filename):
    """下载文件"""
    try:
        # 构建完整的文件路径
        file_path = safe_join(DOWNLOAD_FOLDER, filename)

        # 安全检查
        if not os.path.isfile(file_path):
            return "文件不存在", 404

        # 获取目录和文件名
        directory = os.path.dirname(file_path)
        filename_only = os.path.basename(file_path)

        # 记录下载日志
        client_ip = request.remote_addr
        logging.info(f"文件下载: {filename} - 客户端: {client_ip}")

        return send_from_directory(
            directory,
            filename_only,
            as_attachment=True,
            download_name=os.path.basename(filename)
        )

    except Exception as e:
        logging.error(f"下载错误: {e}")
        return f"下载错误: {e}", 500


if __name__ == '__main__':
    print("=" * 50)
    print("内网文件下载服务器启动")
    print(f"文件目录: {os.path.abspath(DOWNLOAD_FOLDER)}")
    print("=" * 50)

    app.run(host='0.0.0.0', port=8080, debug=False)
