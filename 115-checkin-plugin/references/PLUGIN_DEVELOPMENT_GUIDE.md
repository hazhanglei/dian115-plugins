# DIAN115 插件开发规范

本文档是 DIAN115 插件开发的核心规范，包含架构设计、权限模型、API 接口和最佳实践。

## 1. 架构概览

DIAN115 插件采用**进程内 WASM 隔离模型**：

```
┌─────────────────────────────────────────────────────────┐
│                    DIAN115 主进程                        │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐ │
│  │  Plugin     │    │  Capability │    │  Host       │ │
│  │  Center     │───▶│   Broker    │───▶│  API        │ │
│  │  (管理员UI)  │    │             │    │  (内部模块)  │ │
│  └─────────────┘    └─────────────┘    └─────────────┘ │
│         │                   │                   │        │
│         ▼                   ▼                   ▼        │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐ │
│  │  Installer  │    │  WASM       │    │  Scheduler  │ │
│  │  (签名验证)  │    │  Runtime    │    │  (定时任务)  │ │
│  └─────────────┘    └─────────────┘    └─────────────┘ │
└─────────────────────────────────────────────────────────┘
```

**关键设计**：
- 插件代码随 `.d115p` 包安装，运行在 DIAN115 主进程的 WASM 沙箱内
- 不依赖 Docker、外部 HTTP 服务、base URL 或远程运行时
- 通过 `dian115.host_call` 进程内调用 Host Broker，不暴露内部路由

## 2. 插件包结构

```
package.d115p (ZIP格式)
├── manifest.json              # 必需：元数据与权限声明
├── integrity.json             # 必需：载荷文件 SHA-256 清单
├── signature.json             # 必需：Ed25519 签名
├── runtime/plugin.wasm        # 必需：入口 WASM 模块
├── ui/schema.json             # 可选：声明式 UI
├── assets/*                   # 可选：图标和静态资源
└── README.md                  # 建议：面向管理员的说明
```

### 文件命名规范

- 路径分隔符统一使用 `/`
- 所有路径转为 UTF-8 NFC 标准化
- 按 UTF-8 字节序升序排列
- 禁止绝对路径、驱动器前缀、反斜杠、`..`、NUL 字节

## 3. Manifest 规范

### 3.1 必需字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `schema_version` | integer | 当前固定为 1 |
| `id` | string | 插件唯一标识，小写反向域名格式 |
| `name` | string | 插件显示名称 |
| `version` | string | SemVer 版本 |
| `runtime.kind` | string | 固定为 `wasm` |
| `runtime.entry` | string | WASM 入口文件路径 |
| `runtime.abi` | string | 固定为 `dian115:plugin@1` |
| `permissions.capabilities` | array | 能力声明列表 |
| `permissions.account_access` | array | 账号访问模式 |

### 3.2 能力声明示例

```json
{
  "permissions": {
    "capabilities": [
      {
        "capability": "network.http",
        "reason": "访问外部签到服务"
      },
      {
        "capability": "scheduler.register",
        "reason": "定时执行签到任务"
      },
      {
        "capability": "notifications.plugin.send",
        "reason": "发送签到结果通知"
      }
    ],
    "account_access": ["main"]
  }
}
```

### 3.3 定时任务声明

```json
{
  "jobs": [
    {
      "id": "daily-checkin",
      "name": "每日签到",
      "default_schedule": "30 9 * * *"
    }
  ]
}
```

**Cron 格式**：五段数字 cron（分、时、日、月、周）
- 支持 `*`、列表、升序范围和步长
- 不支持秒、年份或英文月份/星期名
- 星期取 `0..6`，`0` 为星期日
- 日和星期不能同时限定

## 4. Host API 接口

### 4.1 网络连接

```
POST /plugin-api/v1/network/requests
```

**请求体**：
```json
{
  "url": "https://api.example.com/checkin",
  "method": "POST",
  "headers": {
    "content-type": "application/json"
  },
  "body": {
    "user_id": "abc123"
  },
  "proxy_mode": "system"
}
```

**响应体**：
```json
{
  "success": true,
  "status": 200,
  "data": {
    "result": "signed_in"
  }
}
```

**安全规则**：
- URL 必须使用小写 `https` scheme
- 禁止 `http://`、`ftp://` 等协议
- DNS 解析后拒绝私网/loopback/CGNAT/云元数据
- 响应体上限 2 MiB
- 超时默认 10 秒

### 4.2 账号选择

```
POST /plugin-api/v1/accounts/115/selections
```

**请求体**：
```json
{"mode": "main"}
```
或
```json
{"mode": "backup_pool"}
```
或
```json
{"mode": "backup_ref", "account_ref": "a115_01K..."}
```

**响应体**：
```json
{
  "success": true,
  "account_selection_ref": "asr_xxxxx"
}
```

### 4.3 KV 存储

```
GET    /plugin-api/v1/kv/{key}
PUT    /plugin-api/v1/kv/{key}
DELETE /plugin-api/v1/kv/{key}
GET    /plugin-api/v1/kv
```

**特性**：
- 每个安装实例独立命名空间
- 默认 16 MiB 总容量，单值 256 KiB
- 支持 CAS/version 并发控制
- 插件卸载后数据保留策略由宿主决定

### 4.4 通知发送

```
POST /plugin-api/v1/notifications
```

**请求体**：
```json
{
  "type": "plugin_notification_message",
  "title": "签到完成",
  "message": "用户张三今日已成功签到"
}
```

## 5. WASM 开发规范

### 5.1 ABI 要求

**导入函数**：
```c
// 调用 Host API
i32 host_call(i32 request_ptr, i32 request_len, i32 response_ptr)

// 日志记录
i32 log(i32 level, i32 msg_ptr, i32 msg_len)
```

**导出函数**：
```c
// 入口函数
i32 dian115_invoke(i32 input_ptr, i32 input_len, i32* output_ptr, i32* output_len)

// 内存管理（可选）
i32 dian115_alloc(i32 size)
void  dian115_free(i32 ptr)
```

### 5.2 事件处理

```c
// 事件类型
#define EVENT_CHECKIN_COMPLETED  "checkin.completed"
#define EVENT_CHECKIN_FAILED     "checkin.failed"
#define EVENT_ACCOUNT_CHANGED    "account.changed"

// 事件结构
{
  "event_id": "evt_xxx",
  "topic": "checkin.completed",
  "occurred_at": "2026-01-01T10:00:00Z",
  "data": { ... }
}
```

### 5.3 内存限制

- 默认最大内存：32 MiB
- 硬上限：64 MiB
- 建议：使用 16 MiB 或更小

## 6. 声明式 UI

### 6.1 Schema 结构

```json
{
  "views": [
    {
      "id": "main",
      "title": "签到管理",
      "sections": [
        {
          "type": "status",
          "id": "status",
          "title": "签到状态",
          "fields": [
            {"key": "today_signed", "label": "今日签到"}
          ]
        },
        {
          "type": "form",
          "id": "config",
          "title": "签到配置",
          "fields": [
            {
              "key": "checkin_time",
              "type": "text",
              "label": "签到时间"
            }
          ]
        },
        {
          "type": "actions",
          "id": "actions",
          "title": "操作",
          "buttons": [
            {"id": "test_checkin", "label": "测试签到", "action": "test_checkin"}
          ]
        }
      ]
    }
  ]
}
```

### 6.2 支持的 Section 类型

| 类型 | 说明 |
|---|---|
| `status` | 状态展示，键值对 |
| `form` | 表单，支持多种控件 |
| `table` | 表格，展示列表数据 |
| `log` | 日志展示 |
| `progress` | 进度条 |
| `actions` | 操作按钮 |

### 6.3 支持的控件类型

| 类型 | 说明 |
|---|---|
| `text` | 单行文本输入 |
| `textarea` | 多行文本输入 |
| `number` | 数值输入 |
| `switch` | 开关 |
| `select` | 下拉选择 |
| `multiselect` | 多选 |
| `secret-ref` | 托管凭据引用 |
| `file-picker` | 文件选择器 |
| `directory-picker` | 目录选择器 |

## 7. 打包校验清单

### 7.1 静态安全检查

- [ ] 无绝对路径、驱动器前缀、反斜杠
- [ ] 无 `..` 路径遍历
- [ ] 无 NUL 字节
- [ ] 无 Unicode NFC/case-fold 冲突
- [ ] 无符号链接、硬链接、设备文件
- [ ] 无 DOS 设备名（CON/PRN/AUX/NUL/COM1..9/LPT1..9）
- [ ] 无 ADS（`:DATA` 后缀）
- [ ] 无尾随点或空格

### 7.2 大小限制检查

- [ ] 压缩包 ≤ 32 MiB
- [ ] 解压后总量 ≤ 128 MiB
- [ ] 文件数量 ≤ 1024
- [ ] 单个非 WASM 文件 ≤ 32 MiB
- [ ] WASM 入口模块 ≤ 16 MiB
- [ ] 清单大小 ≤ 256 KiB

### 7.3 完整性检查

- [ ] `manifest.json` 符合 schema
- [ ] `integrity.json` 所有文件 SHA-256 一致
- [ ] `signature.json` Ed25519 签名有效
- [ ] ZIP 成员与 integrity.json 完全匹配
- [ ] 无未声明的额外文件

### 7.4 功能检查

- [ ] 所有 capability 都有对应 reason
- [ ] `files.cloud.*` 或 `transfer.115.*` 都有 `accounts.115.use`
- [ ] `accounts.115.use` 都有非空 `account_access`
- [ ] 所有 job id 全局唯一
- [ ] 所有 UI view id 全局唯一
- [ ] 同一 view 内 section/form/action id 不重复

## 8. 开发流程

### 8.1 快速开始

```bash
# 1. 创建项目目录
mkdir my-plugin && cd my-plugin

# 2. 编写 manifest.json
cat > manifest.json << 'EOF'
{
  "schema_version": 1,
  "id": "dev.example.my-plugin",
  "name": "My Plugin",
  "version": "0.1.0",
  "runtime": {
    "kind": "wasm",
    "entry": "runtime/plugin.wasm",
    "abi": "dian115:plugin@1"
  },
  "permissions": {
    "capabilities": [
      {"capability": "network.http", "reason": "访问外部服务"}
    ]
  }
}
EOF

# 3. 编写 WASM 代码（Rust 示例）
mkdir -p runtime
cat > runtime/src/lib.rs << 'EOF'
#[wasm_bindgen]
pub extern "C" fn dian115_invoke(
    input_ptr: u32,
    input_len: u32,
    output_ptr: *mut u32,
    output_len: *mut u32,
) -> i32 {
    // 处理逻辑
    0
}
EOF

# 4. 编译 WASM
tinygo build -o runtime/plugin.wasm -target wasm ./runtime/src/lib.rs

# 5. 生成完整性校验
python3 devtools.py build

# 6. 测试安装
# 将 .d115p 文件上传到 DIAN115 插件中心
```

### 8.2 调试技巧

1. **日志输出**：使用 `dian115.log` 导出调试信息
2. **健康检查**：通过管理端 `/runtime/health-check` 验证
3. **状态查看**：通过 `/runtime/state` 查看 UI 状态
4. **事件调试**：通过 `/runtime/events` 手动投递测试事件

## 9. 常见错误

### 9.1 安装失败

| 错误 | 原因 | 解决方案 |
|---|---|---|
| `invalid_capability` | 能力声明无效 | 检查 capabilities 是否在允许列表 |
| `missing_reason` | 缺少原因说明 | 为每个 capability 添加 reason |
| `account_access_missing` | 缺少账号访问声明 | 添加 account_access 字段 |
| `signature_invalid` | 签名验证失败 | 检查 Ed25519 签名流程 |
| `integrity_mismatch` | SHA-256 不一致 | 重新计算所有文件哈希 |

### 9.2 运行时错误

| 错误 | 原因 | 解决方案 |
|---|---|---|
| `memory_limit_exceeded` | 内存超限 | 优化内存使用 |
| `timeout` | 调用超时 | 增加 timeout_ms 或优化逻辑 |
| `capability_denied` | 能力未授权 | 检查 manifest 声明 |
| `account_context_mismatch` | 混用账号引用 | 统一使用同一 account_selection_ref |

## 10. 最佳实践

### 10.1 安全规范

1. **不信任外部输入**：所有参数必须校验
2. **敏感数据脱敏**：分享码、凭据等在日志中脱敏
3. **幂等性保证**：所有写操作使用稳定幂等键
4. **最小权限原则**：只声明实际需要的能力

### 10.2 性能优化

1. **内存控制**：保持在线性内存 < 16 MiB
2. **超时设置**：根据实际延迟设置合理超时
3. **缓存策略**：合理使用 KV 存储缓存状态
4. **批量操作**：大任务使用异步 job 模式

### 10.3 用户体验

1. **清晰的状态反馈**：及时更新 UI 状态
2. **友好的错误提示**：将技术错误转化为用户可理解的信息
3. **进度展示**：长时间操作显示进度
4. **确认提示**：破坏性操作前显示确认

## 11. 参考资源

- 完整 Schema：`manifest.schema.json`、`integrity.schema.json`、`signature.schema.json`
- OpenAPI：`openapi-v1.yaml`
- 官方仓库：`madbrolab/dian115/plugin-market/`
- 开发者指南：`developer-guide.md`
