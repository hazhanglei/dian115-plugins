# 115频道签到助手

## 功能概述

115频道群组自动签到管理插件，支持：

- **签到规则管理**：配置签到时间、条件
- **定时签到**：自动执行每日签到任务
- **签到通知**：Telegram/插件通知
- **签到统计**：连续签到天数、总签到天数

## 安装

1. 生成签名证书
2. 编译 WASM 模块
3. 打包为 `.d115p`
4. 在 DIAN115 插件中心安装

## 配置

```json
{
  "checkin_time": "09:30",
  "notification_enabled": true,
  "stats_enabled": true
}
```

## 定时任务

- `daily-checkin`: 每日 09:30 执行签到
- `checkin-stats`: 每日 21:00 发送统计报告

## 依赖

- DIAN115 >= 3.9.0
- Plugin API ^1.0
