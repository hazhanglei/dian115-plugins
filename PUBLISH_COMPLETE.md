# DIAN115 插件发布完成

## 发布信息

| 项目 | 值 |
|---|---|
| GitHub 仓库 | https://github.com/hazhanglei/dian115-plugins |
| Release | https://github.com/hazhanglei/dian115-plugins/releases/tag/v0.1.0 |
| 市场索引 | https://raw.githubusercontent.com/hazhanglei/dian115-plugins/main/plugin-market/index.json |
| 插件包 | dev.zl.115-checkin-0.1.0.d115p |
| SHA-256 | `3fc5ad1ca206a2bab21684d1cceaa5f006fe21874904c459d0dab10d5344e0bb` |

## 添加为自定义仓库

在 DIAN115 插件中心添加以下仓库地址：

```
https://github.com/hazhanglei/dian115-plugins
```

服务端会自动解析为：
```
https://raw.githubusercontent.com/hazhanglei/dian115-plugins/main/plugin-market/index.json
```

## 安装方式

1. 打开 DIAN115 管理界面
2. 进入「插件中心」
3. 添加自定义仓库：`https://github.com/hazhanglei/dian115-plugins`
4. 刷新仓库，找到「115频道签到助手」
5. 点击安装，确认权限声明
6. 启用插件

## 下一步

1. 安装 TinyGo 后编译 WASM 模块
2. 实际接入 115 签到 API
3. 测试签到功能
4. 完善通知配置
