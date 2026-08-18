# 115频道签到助手 - 集成与使用说明

## 一、插件信息

| 项目 | 值 |
|---|---|
| 插件 ID | `dev.zl.115-checkin` |
| 版本 | `0.1.0` |
| 名称 | 115频道签到助手 |
| 作者 | ZL |
| 运行时 | WASM (dian115:plugin@1) |
| 内存限制 | 16 MiB |
| 超时限制 | 8 秒 |

## 二、功能特性

### 2.1 签到规则管理
- 配置每日签到时间（默认 09:30）
- 启用/禁用签到通知
- 启用/禁用每日统计报告

### 2.2 定时任务
| 任务 ID | 执行时间 | 说明 |
|---|---|---|
| `daily-checkin` | 每日 09:30 | 自动执行签到 |
| `checkin-stats` | 每日 21:00 | 发送签到统计 |

### 2.3 通知推送
- 签到成功通知
- 签到失败通知
- 每日统计报告

## 三、权限声明

| 能力 | 用途 |
|---|---|
| `network.http` | 访问 115 签到 API |
| `storage.kv` | 存储签到记录和配置 |
| `scheduler.register` | 定时执行签到任务 |
| `notifications.plugin.send` | 发送签到通知 |
| `events.subscribe` | 接收账号变更等事件 |

账号访问模式：主账号、备用号池、指定备用账号

## 四、安装步骤

### 4.1 前置条件

1. DIAN115 >= 3.9.0
2. Plugin API ^1.0
3. Ed25519 开发者密钥对

### 4.2 编译 WASM

```bash
# 使用 TinyGo 编译
tinygo build -o runtime/plugin.wasm \
    -target wasm \
    -no-debug \
    runtime/plugin.go

# 或使用 Rust + tinygo
cargo tinygo build --release --target wasm32-unknown-unknown
```

### 4.3 生成签名

```bash
# 使用 Ed25519 签名工具
python3 scripts/sign_plugin.py \
    --manifest manifest.json \
    --private-key private.key \
    --output signature.json
```

### 4.4 构建插件包

```bash
python3 build.py
# 输出: dist/dev.zl.115-checkin-0.1.0.d115p
```

### 4.5 安装到 DIAN115

1. 打开 DIAN115 管理界面
2. 进入「插件中心」→「已安装」
3. 点击「安装插件」
4. 上传 `dev.zl.115-checkin-0.1.0.d115p`
5. 确认能力声明并安装
6. 启用插件

## 五、配置说明

### 5.1 通过 UI 配置

在插件管理界面的「声明式 UI」中：

1. 设置签到时间（格式：HH:MM）
2. 启用/禁用签到通知
3. 启用/禁用每日统计
4. 点击「测试签到」验证配置

### 5.2 通过 API 配置

```bash
# 获取当前配置
curl -X POST http://localhost:8080/plugin-api/v1/kv/config \
  -H "Content-Type: application/json" \
  -d '{"action": "get"}'

# 设置配置
curl -X POST http://localhost:8080/plugin-api/v1/kv/config \
  -H "Content-Type: application/json" \
  -d '{
    "action": "set",
    "value": {
      "checkin_time": "09:30",
      "notification_enabled": true,
      "stats_enabled": true
    }
  }'
```

## 六、API 使用示例

### 6.1 手动触发签到

```bash
# 调用插件 action
curl -X POST http://localhost:8080/plugin-api/v1/runtime/actions/test_checkin
```

### 6.2 获取签到统计

```bash
# 调用插件内部函数
curl -X POST http://localhost:8080/plugin-api/v1/kv/stats \
  -H "Content-Type: application/json" \
  -d '{"action": "get"}'
```

### 6.3 查看签到记录

```bash
# 获取最近 7 天签到记录
curl -X GET "http://localhost:8080/plugin-api/v1/kv/records?days=7"
```

## 七、事件处理

### 7.1 签到完成事件

```json
{
  "event_id": "evt_abc123",
  "topic": "checkin.completed",
  "occurred_at": "2026-08-18T09:30:00Z",
  "data": {
    "user_id": "user_123",
    "timestamp": 1723972200,
    "result": "success"
  }
}
```

### 7.2 签到失败事件

```json
{
  "event_id": "evt_def456",
  "topic": "checkin.failed",
  "occurred_at": "2026-08-18T09:30:00Z",
  "data": {
    "user_id": "user_123",
    "error": "network_timeout",
    "retry_count": 3
  }
}
```

## 八、KV 存储结构

### 8.1 配置数据

```
key: plugin:config
value: {
  "checkin_time": "09:30",
  "notification_enabled": true,
  "stats_enabled": true
}
```

### 8.2 签到记录

```
key: plugin:records:{date}
value: [
  {"user_id": "u1", "success": true, "timestamp": 1723972200},
  {"user_id": "u2", "success": false, "error": "timeout"}
]
```

### 8.3 统计缓存

```
key: plugin:stats:daily:{date}
value: {
  "total": 100,
  "success": 95,
  "failed": 5,
  "streak": 7
}
```

## 九、故障排查

### 9.1 签到失败

**可能原因**：
1. 网络不通
2. 账号失效
3. API 接口变更

**排查步骤**：
1. 检查网络连通性
2. 验证账号状态
3. 查看日志输出

### 9.2 定时任务未执行

**可能原因**：
1. 插件未启用
2. Cron 配置错误
3. 时区不一致

**排查步骤**：
1. 确认插件状态为「启用」
2. 检查 cron 表达式格式
3. 核对系统时区设置

### 9.3 通知未发送

**可能原因**：
1. Telegram 配置缺失
2. 通知权限未授权

**排查步骤**：
1. 检查管理员配置中的 Telegram 设置
2. 确认插件有 `notifications.plugin.send` 权限

## 十、升级指南

### 10.1 版本兼容性

| 版本 | 兼容性 | 变更内容 |
|---|---|---|
| 0.1.0 | 基础版 | 初始版本，支持基本签到功能 |

### 10.2 升级步骤

1. 备份当前配置和数据
2. 下载新版本 `.d115p`
3. 在插件中心选择「更新」
4. 重新确认能力声明
5. 等待安装完成

## 十一、开发资源

### 11.1 文件结构

```
115-checkin-plugin/
├── manifest.json              # 插件清单
├── integrity.json             # 文件完整性校验
├── signature.json             # Ed25519 签名
├── runtime/
│   └── plugin.wasm           # WASM 模块
├── ui/
│   └── schema.json           # 声明式 UI
├── assets/
│   └── icon.png              # 插件图标
├── README.md                  # 使用说明
├── build.py                   # 构建脚本
├── devtools.py                # 开发工具
└── references/
    └── PLUGIN_DEVELOPMENT_GUIDE.md  # 开发指南
```

### 11.2 工具命令

```bash
# 验证 manifest
python3 devtools.py validate --manifest manifest.json

# 构建插件包
python3 build.py

# 查看插件信息
python3 devtools.py info --package dist/*.d115p
```

## 十二、许可协议

MIT License - 参见 [LICENSE](../LICENSE) 文件

---

**最后更新**: 2026-08-18
**维护者**: ZL
