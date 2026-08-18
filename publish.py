#!/usr/bin/env python3
"""
DIAN115 插件仓库发布脚本

用法:
    python3 publish.py [--plugin-dir DIR] [--version VER] [--skip-compile]

示例:
    python3 publish.py --plugin-dir ./plugins/115-checkin-plugin
    python3 publish.py --skip-compile
"""

import json
import hashlib
import zipfile
import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime


def sha256_file(filepath: str) -> str:
    """计算文件 SHA-256"""
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def compile_wasm(source_path: str, output_path: str) -> bool:
    """使用 TinyGo 编译 WASM"""
    try:
        result = subprocess.run(
            ['tinygo', 'build', '-o', output_path, '-target', 'wasm', '-no-debug', source_path],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"✓ WASM 编译成功: {output_path}")
            return True
        else:
            print(f"✗ WASM 编译失败: {result.stderr}")
            return False
    except FileNotFoundError:
        print("错误: TinyGo 未安装，请先安装 TinyGo")
        print("安装命令: https://tinygo.org/getting-started/install/")
        return False


def create_plugin_package(plugin_dir: str, output_dir: str) -> tuple:
    """创建插件包"""
    plugin_path = Path(plugin_dir).resolve()
    output_path = Path(output_dir).resolve()
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 加载 manifest
    manifest_path = plugin_path / 'manifest.json'
    if not manifest_path.exists():
        raise FileNotFoundError(f"manifest.json not found: {manifest_path}")
    
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
        zf.write(manifest_path, 'manifest.json')
        zf.write(integrity_path, 'integrity.json')
        
        sig_path = plugin_path / 'signature.json'
        if sig_path.exists():
            zf.write(sig_path, 'signature.json')
        
        if wasm_path.exists():
            zf.write(wasm_path, 'runtime/plugin.wasm')
        
        if ui_path.exists():
            zf.write(ui_path, 'ui/schema.json')
        
        if icon_path.exists():
            zf.write(icon_path, 'assets/icon.png')
        
        readme_path = plugin_path / 'README.md'
        if readme_path.exists():
            zf.write(readme_path, 'README.md')
    
    pkg_size = pkg_path.stat().st_size
    print(f"✓ 插件包创建成功: {pkg_path} ({pkg_size} bytes)")
    
    return str(pkg_path), manifest.get('id'), manifest.get('version')


def update_market_index(repo_root: str, plugin_id: str, version: str, package_path: str):
    """更新 plugin-market/index.json"""
    index_path = Path(repo_root) / 'plugin-market' / 'index.json'
    
    # 加载现有索引
    if index_path.exists():
        with open(index_path, 'r', encoding='utf-8') as f:
            index = json.load(f)
    else:
        index = {
            "schema_version": 1,
            "repository": {
                "id": "placeholder",
                "name": "Placeholder Market",
                "homepage": "https://github.com/placeholder/dian115-plugins"
            },
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "plugins": []
        }
    
    # 计算包 SHA-256
    package_sha256 = sha256_file(package_path)
    
    # 查找或创建插件条目
    plugin_entry = None
    for p in index.get('plugins', []):
        if p.get('id') == plugin_id:
            plugin_entry = p
            break
    
    if plugin_entry is None:
        plugin_entry = {
            "id": plugin_id,
            "name": plugin_id.split('.')[-1].title(),
            "version": version,
            "description": "",
            "author": "Unknown",
            "homepage": "",
            "package_url": f"https://github.com/placeholder/dian115-plugins/releases/download/v{version}/{plugin_id}-{version}.d115p",
            "sha256": package_sha256,
            "capabilities": [],
            "account_access": [],
            "min_dian115": "3.9.0",
            "published_at": datetime.utcnow().isoformat() + "Z"
        }
        if 'plugins' not in index:
            index['plugins'] = []
        index['plugins'].append(plugin_entry)
    else:
        # 更新现有条目
        plugin_entry['version'] = version
        plugin_entry['sha256'] = package_sha256
        plugin_entry['package_url'] = f"https://github.com/placeholder/dian115-plugins/releases/download/v{version}/{plugin_id}-{version}.d115p"
        plugin_entry['published_at'] = datetime.utcnow().isoformat() + "Z"
    
    # 更新 repository 信息
    if 'repository' not in index:
        index['repository'] = {}
    index['generated_at'] = datetime.utcnow().isoformat() + "Z"
    
    # 保存索引
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=2, ensure_ascii=False)
    
    print(f"✓ 市场索引已更新: {index_path}")
    return index


def create_github_release(repo_name: str, version: str, package_path: str):
    """创建 GitHub Release 并上传插件包"""
    cmd = [
        'gh', 'release', 'create',
        f'v{version}',
        '--title', f'Version {version}',
        '--notes', f'Release version {version} of DIAN115 plugins',
        package_path
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ GitHub Release 创建成功: v{version}")
            return True
        else:
            print(f"✗ GitHub Release 创建失败: {result.stderr}")
            return False
    except FileNotFoundError:
        print("错误: gh CLI 未安装，请先安装 GitHub CLI")
        print("安装命令: https://cli.github.com/")
        return False


def main():
    print("=" * 50)
    print("DIAN115 插件仓库发布脚本")
    print("=" * 50)
    
    # 仓库根目录（脚本所在目录）
    repo_root = str(Path(__file__).parent.resolve())
    
    # 解析参数
    plugin_dir = None
    version = None
    skip_compile = False
    
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == '--plugin-dir' and i + 1 < len(args):
            plugin_dir = args[i + 1]
            i += 2
        elif args[i] == '--version' and i + 1 < len(args):
            version = args[i + 1]
            i += 2
        elif args[i] == '--skip-compile':
            skip_compile = True
            i += 1
        else:
            i += 1
    
    # 默认插件目录（相对于仓库根目录）
    if not plugin_dir:
        plugin_dir = os.path.join(repo_root, 'plugins', '115-checkin-plugin')
    
    plugin_dir = str(Path(plugin_dir).resolve())
    
    # 版本
    if not version:
        manifest_path = os.path.join(plugin_dir, 'manifest.json')
        if os.path.exists(manifest_path):
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
                version = manifest.get('version', '0.1.0')
        else:
            version = '0.1.0'
    
    # 插件 ID
    plugin_id = None
    manifest_path = os.path.join(plugin_dir, 'manifest.json')
    if os.path.exists(manifest_path):
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
            plugin_id = manifest.get('id')
    
    print(f"\n仓库根目录: {repo_root}")
    print(f"插件目录: {plugin_dir}")
    print(f"插件 ID: {plugin_id}")
    print(f"版本: {version}")
    
    # 步骤 1: 编译 WASM
    if not skip_compile:
        print("\n[1/4] 编译 WASM 模块...")
        source_path = os.path.join(plugin_dir, 'runtime', 'plugin.go')
        output_path = os.path.join(plugin_dir, 'runtime', 'plugin.wasm')
        
        if os.path.exists(source_path):
            if not compile_wasm(source_path, output_path):
                print("跳过 WASM 编译（编译失败，将继续使用现有文件）")
        else:
            print(f"WASM 源码不存在: {source_path}，跳过编译")
    
    # 步骤 2: 创建插件包
    print("\n[2/4] 创建插件包...")
    dist_dir = os.path.join(plugin_dir, 'dist')
    package_path, pid, pver = create_plugin_package(plugin_dir, dist_dir)
    
    # 步骤 3: 更新市场索引
    print("\n[3/4] 更新市场索引...")
    index = update_market_index(repo_root, plugin_id or pid, version or pver, package_path)
    
    # 步骤 4: 创建 GitHub Release
    print("\n[4/4] GitHub Release")
    print("注意: 需要配置 gh CLI 并登录 GitHub")
    print("命令: gh auth login")
    
    # 创建 Release（可选）
    if input("\n是否创建 GitHub Release? (y/n): ").lower() == 'y':
        repo_name = input("请输入 GitHub 仓库名 (如 username/repo): ")
        create_github_release(repo_name, version or pver, package_path)
    
    print("\n" + "=" * 50)
    print("发布完成!")
    print(f"插件包: {package_path}")
    print(f"市场索引: {os.path.join(repo_root, 'plugin-market', 'index.json')}")
    print("=" * 50)


if __name__ == '__main__':
    main()
