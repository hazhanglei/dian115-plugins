# 115频道签到助手 - 项目归档

## 项目概述

**插件名称**: 115频道签到助手  
**插件 ID**: `dev.zl.115-checkin`  
**版本**: 0.1.0  
**开发日期**: 2026-08-18  
**开发者**: ZL

## 功能特性

### 核心功能
1. **签到规则管理**
   - 配置每日签到时间
   - 启用/禁用通知推送
   - 启用/禁用统计报告

2. **定时签到任务**
   - 每日 09:30 自动执行签到
   - 每日 21:00 发送统计报告

3. **签到通知**
   - 签到成功通知
   - 签到失败告警
   - 每日签到统计

## 文件清单

| 文件 | 大小 | 说明 |
|---|---|---|
| `manifest.json` | 1.8 KB | 插件清单与权限声明 |
| `integrity.json` | 0.5 KB | 文件完整性校验 |
| `signature.json` | 0.1 KB | Ed25519 签名（占位） |
| `runtime/plugin.go` | 5.3 KB | WASM 源代码 |
| `ui/schema.json` | 1.6 KB | 声明式 UI 配置 |
| `assets/icon.png` | 0 KB | 插件图标（占位） |
| `README.md` | 0.7 KB | 使用说明 |
| `build.py` | 4.2 KB | Windows 构建脚本 |
| `devtools.py` | 10 KB | 开发工具集 |
| `INTEGRATION_GUIDE.md` | 6.2 KB | 集成指南 |
| `references/PLUGIN_DEVELOPMENT_GUIDE.md` | 12.4 KB | 开发规范 |

## 构建产物

```
dist/dev.zl.115-checkin-0.1.0.d115p (2.7 KB)
```

## 权限声明

| 能力 | 用途 |
|---|---|
| `network.http` | 访问 115 签到 API |
| `storage.kv` | 存储签到记录和配置 |
| `scheduler.register` | 定时执行签到任务 |
| `notifications.plugin.send` | 发送签到通知 |
| `events.subscribe` | 接收账号变更等事件 |

账号访问模式：主账号、备用号池、指定备用账号

## 后续步骤

### 待完成
1. [ ] 生成 Ed25519 密钥对
2. [ ] 编译 WASM 模块（需要 TinyGo 环境）
3. [ ] 签署插件包
4. [ ] 实际接入 115 签到 API
5. [ ] 测试验证

### 环境依赖
- TinyGo ≥ 0.30（用于编译 WASM）
- Python 3.11+（用于构建脚本）

## 技术栈

- **运行时**: WASM (wazero)
- **ABI**: dian115:plugin@1
- **内存限制**: 16 MiB
- **超时限制**: 8 秒

## 参考资源

- DIAN115 插件开发规范
- Plugin API v1 契约
- Host API 文档

---

**归档日期**: 2026-08-18  
**归档路径**: E:\Hermes\00-配置档案总库\默认配置\04-成品导出目录\plugins\115-checkin-plugin\
