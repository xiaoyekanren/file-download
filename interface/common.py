# coding=utf-8
import os
import logging
from datetime import datetime
from pathlib import Path
import urllib.parse


def get_file_info(file_path):
    """获取文件的详细信息"""
    stat = os.stat(file_path)
    size_bytes = os.path.getsize(file_path)
    return {
        'size': get_file_size(file_path),
        'size_bytes': size_bytes,
        'mtime': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
        'mtime_raw': datetime.fromtimestamp(stat.st_mtime).isoformat(),
        'extension': Path(file_path).suffix[1:].upper() if Path(file_path).suffix else '未知'
    }


def get_file_size(file_path):
    """获取文件大小并格式化为易读格式"""
    size = os.path.getsize(file_path)
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"


def get_folder_info(folder_path):
    """获取文件夹的详细信息"""
    stat = os.stat(folder_path)
    file_count = sum(1 for _ in os.scandir(folder_path) if _.is_file())
    return {
        'mtime': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
        'file_count': file_count
    }


def list_directory(directory_path, base_path=None):
    """列出指定目录的内容"""
    if base_path is None:
        base_path = directory_path

    folders = []
    files = []

    try:
        for item in os.listdir(directory_path):
            item_path = os.path.join(directory_path, item)
            relative_path = os.path.relpath(item_path, base_path)

            if os.path.isfile(item_path):
                file_info = get_file_info(item_path)
                files.append({
                    'name': item,
                    'relative_path': relative_path,
                    'full_path': item_path,
                    **file_info
                })
            elif os.path.isdir(item_path):
                folder_info = get_folder_info(item_path)
                folders.append({
                    'name': item,
                    'relative_path': relative_path,
                    'full_path': item_path,
                    'url': '/' + urllib.parse.quote(relative_path.replace(os.sep, '/')),
                    **folder_info
                })

    except PermissionError as e:
        logging.warning(f"没有权限访问目录: {directory_path} - {e}")
    except Exception as e:
        logging.error(f"读取目录错误: {directory_path} - {e}")

    # 排序：文件夹在前，文件在后，都按名称排序
    folders.sort(key=lambda x: x['name'].lower())
    files.sort(key=lambda x: x['name'].lower())

    return folders, files


def get_breadcrumbs(current_path, base_path):
    """生成面包屑导航"""
    breadcrumbs = [{'name': '📁 根目录', 'url': '/'}]

    if current_path == base_path:
        return breadcrumbs

    # 计算相对于基路径的相对路径
    rel_path = os.path.relpath(current_path, base_path)
    if rel_path == '.':
        return breadcrumbs

    # 分割路径为各个部分
    parts = rel_path.split(os.sep)

    # 构建每个部分的URL
    current_url = ""
    for part in parts:
        current_url = os.path.join(current_url, part)
        breadcrumbs.append({
            'name': part,
            'url': f'/{urllib.parse.quote(current_url.replace(os.sep, "/"))}'
        })
    return breadcrumbs

