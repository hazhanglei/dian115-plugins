#!/usr/bin/env python3
"""
115频道签到助手 - Windows 构建脚本
生成完整的插件包
"""

import json
import hashlib
import zipfile
import os
import sys
import shutil
from pathlib import Path
from datetime import datetime


def sha256_file(filepath: str) -> str:
    """计算文件 SHA-256"""
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def create_plugin_package(plugin_dir: str, output_dir: str) -> str:
    """创建插件包"""
    plugin_path = Path(plugin_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 加载 manifest
    manifest_path = plugin_path / 'manifest.json'
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)
    
    # 计算所有文件的 hash
    files_info = []
    
    # manifest.json
    files_info.append({
        "path": "manifest.json",
        "size": os.path.getsize(manifest_path),
        "sha256": sha256_file(str(manifest_path))
    })
    
    # runtime/plugin.wasm
    wasm_path = plugin_path / 'runtime' / 'plugin.wasm'
    if wasm_path.exists():
        files_info.append({
            "path": "runtime/plugin.wasm",
            "size": os.path.getsize(wasm_path),
            "sha256": sha256_file(str(wasm_path))
        })
    
    # ui/schema.json
    ui_path = plugin_path / 'ui' / 'schema.json'
    if ui_path.exists():
        files_info.append({
            "path": "ui/schema.json",
            "size": os.path.getsize(ui_path),
            "sha256": sha256_file(str(ui_path))
        })
    
    # assets/icon.png
    icon_path = plugin_path / 'assets' / 'icon.png'
    if icon_path.exists():
        files_info.append({
            "path": "assets/icon.png",
            "size": os.path.getsize(icon_path),
            "sha256": sha256_file(str(icon_path))
        })
    
    # 按 path 排序
    files_info.sort(key=lambda x: x['path'])
    
    # 写入 integrity.json
    integrity = {"files": files_info}
    integrity_path = plugin_path / 'integrity.json'
    with open(integrity_path, 'w', encoding='utf-8') as f:
        json.dump(integrity, f, indent=2, ensure_ascii=False)
    
    # 创建 ZIP 包
    pkg_name = f"{manifest['id']}-{manifest['version']}.d115p"
    pkg_path = output_path / pkg_name
    
    with zipfile.ZipFile(pkg_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        # 添加必需文件
        zf.write(manifest_path, 'manifest.json')
        zf.write(integrity_path, 'integrity.json')
        
        sig_path = plugin_path / 'signature.json'
        if sig_path.exists():
            zf.write(sig_path, 'signature.json')
        
        # 添加 WASM 模块
        if wasm_path.exists():
            zf.write(wasm_path, 'runtime/plugin.wasm')
        
        # 添加 UI schema
        if ui_path.exists():
            zf.write(ui_path, 'ui/schema.json')
        
        # 添加资源
        if icon_path.exists():
            zf.write(icon_path, 'assets/icon.png')
        
        # 添加 README
        readme_path = plugin_path / 'README.md'
        if readme_path.exists():
            zf.write(readme_path, 'README.md')
    
    # 校验包大小
    pkg_size = pkg_path.stat().st_size
    print(f"插件包大小: {pkg_size} bytes ({pkg_size/1024:.1f} KB)")
    
    if pkg_size > 33554432:  # 32 MiB
        print("警告: 插件包超过 32 MiB 限制")
    
    return str(pkg_path)


def main():
    plugin_dir = os.path.join(os.path.dirname(__file__))
    output_dir = os.path.join(plugin_dir, 'dist')
    
    print("=== 115频道签到助手构建 ===")
    print(f"插件目录: {plugin_dir}")
    print(f"输出目录: {output_dir}")
    
    pkg_path = create_plugin_package(plugin_dir, output_dir)
    print(f"\n构建完成: {pkg_path}")
    
    # 显示文件信息
    print("\n文件列表:")
    with zipfile.ZipFile(pkg_path, 'r') as zf:
        for info in zf.infolist():
            size_kb = info.file_size / 1024
            print(f"  {info.filename}: {size_kb:.1f} KB")


if __name__ == '__main__':
    main()
