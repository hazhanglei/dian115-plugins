#!/usr/bin/env python3
"""
115频道签到助手 - WASM 插件开发辅助脚本
提供工具函数用于开发、测试和打包插件
"""

import json
import hashlib
import zipfile
import os
import sys
from pathlib import Path
from datetime import datetime


def sha256_file(filepath: str) -> str:
    """计算文件 SHA-256"""
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def load_manifest(manifest_path: str) -> dict:
    """加载 manifest.json"""
    with open(manifest_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def update_integrity(plugin_dir: str, manifest: dict) -> dict:
    """根据实际文件更新 integrity.json"""
    files = []
    
    # manifest.json
    manifest_path = os.path.join(plugin_dir, 'manifest.json')
    files.append({
        "path": "manifest.json",
        "size": os.path.getsize(manifest_path),
        "sha256": sha256_file(manifest_path)
    })
    
    # runtime/plugin.wasm
    wasm_path = os.path.join(plugin_dir, 'runtime', 'plugin.wasm')
    if os.path.exists(wasm_path):
        files.append({
            "path": "runtime/plugin.wasm",
            "size": os.path.getsize(wasm_path),
            "sha256": sha256_file(wasm_path)
        })
    
    # ui/schema.json
    ui_path = os.path.join(plugin_dir, 'ui', 'schema.json')
    if os.path.exists(ui_path):
        files.append({
            "path": "ui/schema.json",
            "size": os.path.getsize(ui_path),
            "sha256": sha256_file(ui_path)
        })
    
    # assets/icon.png
    icon_path = os.path.join(plugin_dir, 'assets', 'icon.png')
    if os.path.exists(icon_path):
        files.append({
            "path": "assets/icon.png",
            "size": os.path.getsize(icon_path),
            "sha256": sha256_file(icon_path)
        })
    
    # 按 path 排序
    files.sort(key=lambda x: x['path'])
    
    return {"files": files}


def validate_manifest(manifest: dict) -> list:
    """验证 manifest 结构"""
    errors = []
    
    # 必需字段
    required_fields = ['schema_version', 'id', 'name', 'version', 'runtime', 'permissions']
    for field in required_fields:
        if field not in manifest:
            errors.append(f"缺少必需字段: {field}")
    
    # 验证 schema_version
    if manifest.get('schema_version') != 1:
        errors.append("schema_version 必须为 1")
    
    # 验证 id 格式
    plugin_id = manifest.get('id', '')
    if not plugin_id or not isinstance(plugin_id, str):
        errors.append("plugin id 不能为空")
    elif '/' in plugin_id or '\\' in plugin_id:
        errors.append("plugin id 不能包含路径分隔符")
    
    # 验证 runtime
    runtime = manifest.get('runtime', {})
    if runtime.get('kind') != 'wasm':
        errors.append("runtime.kind 必须为 wasm")
    if runtime.get('abi') != 'dian115:plugin@1':
        errors.append("runtime.abi 必须为 dian115:plugin@1")
    
    # 验证 permissions
    perms = manifest.get('permissions', {})
    capabilities = perms.get('capabilities', [])
    
    for cap in capabilities:
        if 'capability' not in cap:
            errors.append("每个 capability 必须包含 capability 字段")
        if 'reason' not in cap:
            errors.append(f"capability '{cap.get('capability', '')}' 必须包含 reason 字段")
    
    # 验证 schedule
    jobs = manifest.get('jobs', [])
    for job in jobs:
        schedule = job.get('default_schedule', '')
        if schedule:
            parts = schedule.split()
            if len(parts) != 5:
                errors.append(f"job '{job.get('id')}' 的 cron 格式不正确")
    
    return errors


def create_plugin_package(plugin_dir: str, output_dir: str) -> str:
    """创建插件包"""
    plugin_path = Path(plugin_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 加载 manifest
    manifest_path = plugin_path / 'manifest.json'
    manifest = load_manifest(str(manifest_path))
    
    # 验证 manifest
    errors = validate_manifest(manifest)
    if errors:
        print("Manifest 验证错误:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    
    # 更新 integrity.json
    integrity = update_integrity(str(plugin_path), manifest)
    integrity_path = plugin_path / 'integrity.json'
    with open(integrity_path, 'w', encoding='utf-8') as f:
        json.dump(integrity, f, indent=2, ensure_ascii=False)
    
    # 检查 signature.json
    sig_path = plugin_path / 'signature.json'
    if not sig_path.exists():
        print("警告: signature.json 不存在，需要手动生成签名")
        # 创建占位文件
        with open(sig_path, 'w', encoding='utf-8') as f:
            json.dump({
                "key_id": manifest.get('publisher', {}).get('key_id', 'placeholder'),
                "public_key": "placeholder",
                "signature": "placeholder"
            }, f, indent=2)
    
    # 创建 ZIP 包
    pkg_name = f"{manifest['id']}-{manifest['version']}.d115p"
    pkg_path = output_path / pkg_name
    
    with zipfile.ZipFile(pkg_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        # 添加必需文件
        for f in ['manifest.json', 'integrity.json', 'signature.json']:
            fp = plugin_path / f
            if fp.exists():
                zf.write(fp, f)
        
        # 添加 WASM 模块
        wasm_path = plugin_path / 'runtime' / 'plugin.wasm'
        if wasm_path.exists():
            zf.write(wasm_path, 'runtime/plugin.wasm')
        else:
            print(f"警告: {wasm_path} 不存在")
        
        # 添加 UI schema
        ui_path = plugin_path / 'ui' / 'schema.json'
        if ui_path.exists():
            zf.write(ui_path, 'ui/schema.json')
        
        # 添加资源
        assets_dir = plugin_path / 'assets'
        if assets_dir.exists():
            for f in assets_dir.iterdir():
                if f.is_file():
                    zf.write(f, f'assets/{f.name}')
        
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


def show_help():
    """显示帮助信息"""
    print("""
115频道签到助手 - 开发工具

用法:
    python3 devtools.py [命令]

命令:
    build       构建插件包
    validate    验证 manifest
    info        显示插件信息
    help        显示此帮助

示例:
    python3 devtools.py build --plugin-dir ./plugin --output-dir ./dist
    python3 devtools.py validate --manifest ./manifest.json
    python3 devtools.py info --package ./dist/plugin.d115p
""")


def main():
    if len(sys.argv) < 2:
        show_help()
        sys.exit(0)
    
    command = sys.argv[1]
    
    if command == 'build':
        # 解析参数
        plugin_dir = None
        output_dir = None
        
        args = sys.argv[2:]
        i = 0
        while i < len(args):
            if args[i] == '--plugin-dir' and i + 1 < len(args):
                plugin_dir = args[i + 1]
                i += 2
            elif args[i] == '--output-dir' and i + 1 < len(args):
                output_dir = args[i + 1]
                i += 2
            else:
                i += 1
        
        if not plugin_dir:
            plugin_dir = os.path.join(os.path.dirname(__file__))
        if not output_dir:
            output_dir = os.path.join(os.path.dirname(__file__), 'dist')
        
        pkg_path = create_plugin_package(plugin_dir, output_dir)
        print(f"\n构建完成: {pkg_path}")
    
    elif command == 'validate':
        manifest_path = None
        args = sys.argv[2:]
        i = 0
        while i < len(args):
            if args[i] == '--manifest' and i + 1 < len(args):
                manifest_path = args[i + 1]
                i += 2
            else:
                i += 1
        
        if not manifest_path:
            print("错误: 请指定 --manifest 参数")
            sys.exit(1)
        
        manifest = load_manifest(manifest_path)
        errors = validate_manifest(manifest)
        
        if errors:
            print("验证失败:")
            for err in errors:
                print(f"  ✗ {err}")
            sys.exit(1)
        else:
            print("✓ Manifest 验证通过")
            print(f"  ID: {manifest.get('id')}")
            print(f"  版本: {manifest.get('version')}")
            print(f"  能力数: {len(manifest.get('permissions', {}).get('capabilities', []))}")
    
    elif command == 'info':
        pkg_path = None
        args = sys.argv[2:]
        i = 0
        while i < len(args):
            if args[i] == '--package' and i + 1 < len(args):
                pkg_path = args[i + 1]
                i += 2
            else:
                i += 1
        
        if not pkg_path:
            print("错误: 请指定 --package 参数")
            sys.exit(1)
        
        with zipfile.ZipFile(pkg_path, 'r') as zf:
            manifest = json.loads(zf.read('manifest.json'))
            integrity = json.loads(zf.read('integrity.json'))
            
            print(f"插件信息:")
            print(f"  ID: {manifest.get('id')}")
            print(f"  名称: {manifest.get('name')}")
            print(f"  版本: {manifest.get('version')}")
            print(f"  作者: {manifest.get('publisher', {}).get('name')}")
            print(f"\n文件列表:")
            for f in integrity.get('files', []):
                size_kb = f['size'] / 1024
                print(f"  {f['path']}: {size_kb:.1f} KB")
    
    else:
        show_help()


if __name__ == '__main__':
    main()
