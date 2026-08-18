#!/usr/bin/env python3
"""
使用 GitHub API 创建仓库并上传插件包
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


def run_command(cmd: list, workdir: str = None) -> tuple:
    """运行命令并返回结果"""
    full_env = os.environ.copy()
    if workdir is None:
        workdir = os.getcwd()
    
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=workdir, env=full_env)
    return result.returncode, result.stdout, result.stderr


def create_github_repo(token: str, repo_name: str, description: str = ""):
    """使用 GitHub API 创建仓库"""
    url = "https://api.github.com/user/repos"
    
    data = {
        "name": repo_name,
        "description": description,
        "private": False,
        "auto_init": False
    }
    
    cmd = [
        'curl', '-s', '-X', 'POST',
        '-H', f'Authorization: token {token}',
        '-H', 'Content-Type: application/json',
        url,
        '-d', json.dumps(data)
    ]
    
    returncode, stdout, stderr = run_command(cmd)
    
    print(f"API 响应: {stdout[:500]}")
    
    if returncode == 0:
        try:
            result = json.loads(stdout)
            if 'html_url' in result:
                print(f"✓ GitHub 仓库创建成功: {result.get('html_url')}")
                return result.get('ssh_url')
            elif 'message' in result and 'already exists' in result.get('message', '').lower():
                print(f"仓库已存在: {result.get('html_url', repo_name)}")
                return f"git@github.com:hazhanglei/{repo_name}.git"
            else:
                print(f"仓库创建响应异常: {result}")
                return None
        except json.JSONDecodeError:
            print(f"仓库创建响应解析失败: {stdout}")
            return None
    else:
        print(f"✗ 仓库创建失败: {stderr}")
        return None


def push_to_github(local_dir: str, repo_url: str, token: str, github_user: str = "hazhanglei"):
    """推送代码到 GitHub"""
    repo_name = repo_url.split('/')[-1].replace('.git', '')
    
    # 检查是否已有 git 仓库
    git_exists = os.path.exists(os.path.join(local_dir, '.git'))
    
    if not git_exists:
        print("初始化 Git 仓库...")
        run_command(['git', 'init'], workdir=local_dir)
    
    # 添加所有文件
    print("添加文件...")
    run_command(['git', 'add', '.'], workdir=local_dir)
    
    # 检查是否有变更
    returncode, stdout, stderr = run_command(['git', 'status', '--porcelain'], workdir=local_dir)
    if not stdout.strip():
        print("没有需要提交的文件")
        return True
    
    # 提交
    print("提交更改...")
    run_command(['git', 'commit', '-m', 'Initial commit: 115频道签到助手 v0.1.0'], workdir=local_dir)
    run_command(['git', 'branch', '-M', 'main'], workdir=local_dir)
    
    # 添加远程仓库（使用 token）
    remote_url = f"https://{token}@github.com/{github_user}/{repo_name}.git"
    run_command(['git', 'remote', 'add', 'origin', remote_url], workdir=local_dir)
    
    # 推送
    print("推送到 GitHub...")
    returncode, stdout, stderr = run_command(['git', 'push', '-u', 'origin', 'main'], workdir=local_dir)
    
    if returncode == 0:
        print(f"✓ 代码推送成功")
        return True
    else:
        print(f"✗ 推送失败: {stderr}")
        return False


def upload_release_asset(token: str, repo_name: str, version: str, asset_path: str, github_user: str = "hazhanglei"):
    """上传 Release 资产"""
    # 先创建 release
    create_release_cmd = [
        'curl', '-s', '-X', 'POST',
        '-H', f'Authorization: token {token}',
        '-H', 'Content-Type: application/json',
        f'https://api.github.com/repos/{github_user}/{repo_name}/releases',
        '-d', json.dumps({
            "tag_name": f"v{version}",
            "name": f"Version {version}",
            "body": f"Release version {version}"
        })
    ]
    
    returncode, stdout, stderr = run_command(create_release_cmd)
    print(f"创建 Release 响应: {stdout[:300]}")
    
    if returncode != 0:
        print(f"创建 Release 失败: {stderr}")
        return False
    
    # 上传资产
    asset_name = os.path.basename(asset_path)
    upload_cmd = [
        'curl', '-s', '-X', 'POST',
        '-H', f'Authorization: token {token}',
        '-H', f'Content-Type: application/octet-stream',
        f'https://uploads.github.com/repos/{github_user}/{repo_name}/releases/releases/download/v{version}/{asset_name}',
        '--data-binary', f'@{asset_path}'
    ]
    
    returncode, stdout, stderr = run_command(upload_cmd)
    
    if returncode == 0:
        print(f"✓ Release 资产上传成功: {asset_name}")
        return True
    else:
        print(f"✗ 资产上传失败: {stderr}")
        return False


def main():
    print("=" * 50)
    print("DIAN115 插件仓库发布工具")
    print("=" * 50)
    
    # 配置
    token = os.environ.get('GITHUB_TOKEN', '')
    if not token:
        print("错误: 请设置 GITHUB_TOKEN 环境变量")
        sys.exit(1)
    github_user = "hazhanglei"
    repo_name = "dian115-plugins"
    local_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 插件目录可能在不同位置，自动查找
    plugin_dirs = [
        os.path.join(local_dir, '115-checkin-plugin'),
        os.path.join(local_dir, 'plugins', '115-checkin-plugin'),
        os.path.join('E:/Hermes/00-配置档案总库/默认配置/01-专属临时缓存', '115-checkin-plugin')
    ]
    plugin_dir = None
    for d in plugin_dirs:
        if os.path.exists(os.path.join(d, 'manifest.json')):
            plugin_dir = d
            break
    if not plugin_dir:
        print("错误: 找不到插件目录")
        sys.exit(1)
    package_path = os.path.join(plugin_dir, 'dist', 'dev.zl.115-checkin-0.1.0.d115p')
    
    # 步骤 1: 创建仓库
    print("\n[1/3] 创建 GitHub 仓库...")
    ssh_url = create_github_repo(token, repo_name, "DIAN115 第三方插件仓库")
    if not ssh_url:
        print("跳过：仓库创建失败")
        ssh_url = f"git@github.com:{github_user}/{repo_name}.git"
    
    # 步骤 2: 推送代码
    print("\n[2/3] 推送代码到 GitHub...")
    if not push_to_github(local_dir, ssh_url, token, github_user):
        print("代码推送失败，尝试直接推送...")
    
    # 步骤 3: 上传 Release
    if os.path.exists(package_path):
        print("\n[3/3] 上传 Release 资产...")
        upload_release_asset(token, repo_name, "0.1.0", package_path, github_user)
    else:
        print(f"\n警告: 插件包不存在: {package_path}")
    
    print("\n" + "=" * 50)
    print("发布完成!")
    print(f"仓库地址: https://github.com/{github_user}/{repo_name}")
    print(f"市场索引: https://raw.githubusercontent.com/{github_user}/{repo_name}/main/plugin-market/index.json")
    print("=" * 50)


if __name__ == '__main__':
    main()
