#!/usr/bin/env python3
"""单独上传 Release 资产"""

import os
import subprocess
import json

def run_command(cmd: list, workdir: str = None) -> tuple:
    full_env = os.environ.copy()
    if workdir is None:
        workdir = os.getcwd()
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=workdir, env=full_env)
    return result.returncode, result.stdout, result.stderr

token = os.environ.get('GITHUB_TOKEN', '')
if not token:
    print("错误: 请设置 GITHUB_TOKEN 环境变量")
    exit(1)

asset_path = os.path.join(os.path.dirname(__file__), '115-checkin-plugin', 'dist', 'dev.zl.115-checkin-0.1.0.d115p')
asset_name = os.path.basename(asset_path)

print(f"上传资产: {asset_name}")
print(f"路径: {asset_path}")

# 获取 release ID
cmd = [
    'curl', '-s',
    '-H', f'Authorization: token {token}',
    'https://api.github.com/repos/hazhanglei/dian115-plugins/releases/latest'
]
returncode, stdout, stderr = run_command(cmd)
release = json.loads(stdout)
release_id = release.get('id')
print(f"Release ID: {release_id}")

# 上传资产
cmd = [
    'curl', '-s', '-X', 'POST',
    '-H', f'Authorization: token {token}',
    '-H', 'Content-Type: application/octet-stream',
    f'https://uploads.github.com/repos/hazhanglei/dian115-plugins/releases/{release_id}/assets?name={asset_name}',
    '--data-binary', f'@{asset_path}'
]
returncode, stdout, stderr = run_command(cmd)
print(f"上传响应: {stdout}")
if returncode != 0:
    print(f"上传失败: {stderr}")
