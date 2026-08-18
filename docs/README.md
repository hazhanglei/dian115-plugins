# DIAN115 Plugins Repository

DIAN115 第三方插件仓库

## 插件列表

### 115频道签到助手 (`dev.zl.115-checkin`)

**描述**: 115频道群组自动签到管理工具，支持定时签到、通知推送和统计报表。

**版本**: 0.1.0  
**作者**: ZL  
**发布日期**: 2026-08-18

**功能特性**:
- 每日自动签到
- 签到通知推送
- 每日统计报告
- 连续签到统计

**权限声明**:
- `network.http` - 访问 115 签到 API
- `storage.kv` - 存储签到记录和配置
- `scheduler.register` - 定时执行签到任务
- `notifications.plugin.send` - 发送签到通知
- `events.subscribe` - 接收账号变更等事件

**账号访问**: 主账号、备用号池、指定备用账号

---

## 安装方式

### 方式一：从 Releases 下载

访问 [Releases](../../releases) 页面，下载对应版本的 `.d115p` 文件，在 DIAN115 插件中心上传安装。

### 方式二：添加自定义仓库

在 DIAN115 插件中心添加以下仓库地址：

```
https://github.com/zl/dian115-plugins
```

服务端会自动解析为：
```
https://raw.githubusercontent.com/zl/dian115-plugins/main/plugin-market/index.json
```

## 开发指南

参见各插件目录下的 README.md

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可

MIT License
