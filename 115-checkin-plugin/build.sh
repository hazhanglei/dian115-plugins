#!/bin/bash
# 115频道签到插件构建脚本

set -e

PLUGIN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="$PLUGIN_DIR/../dist"

echo "=== 115频道签到助手构建脚本 ==="
echo "插件目录: $PLUGIN_DIR"
echo "输出目录: $OUTPUT_DIR"

# 创建输出目录
mkdir -p "$OUTPUT_DIR"

# 检查 TinyGo 是否安装
if ! command -v tinygo &> /dev/null; then
    echo "错误: TinyGo 未安装，请先安装 TinyGo"
    echo "安装命令: https://tinygo.org/getting-started/install/"
    exit 1
fi

# 编译 WASM 模块
echo ""
echo "==> 编译 WASM 模块..."
tinygo build -o "$OUTPUT_DIR/plugin.wasm" \
    -target wasm \
    -no-debug \
    "$PLUGIN_DIR/runtime/plugin.go"

WASM_SIZE=$(stat -f%z "$OUTPUT_DIR/plugin.wasm" 2>/dev/null || stat -c%s "$OUTPUT_DIR/plugin.wasm" 2>/dev/null)
echo "WASM 大小: ${WASM_SIZE} bytes"

# 校验 WASM 大小限制
if [ "$WASM_SIZE" -gt 16777216 ]; then
    echo "警告: WASM 模块超过 16MiB 限制"
    exit 1
fi

# 生成 SHA-256 校验值
echo ""
echo "==> 计算文件 SHA-256..."
MANIFEST_SHA=$(sha256sum "$PLUGIN_DIR/manifest.json" | cut -d' ' -f1)
WASM_SHA=$(sha256sum "$OUTPUT_DIR/plugin.wasm" | cut -d' ' -f1)
UI_SHA=$(sha256sum "$PLUGIN_DIR/ui/schema.json" | cut -d' ' -f1)
ICON_SHA=$(sha256sum "$PLUGIN_DIR/assets/icon.png" | cut -d' ' -f1)

echo "manifest.json: $MANIFEST_SHA"
echo "plugin.wasm: $WASM_SHA"
echo "ui/schema.json: $UI_SHA"
echo "assets/icon.png: $ICON_SHA"

# 更新 integrity.json
echo ""
echo "==> 更新 integrity.json..."
cat > "$PLUGIN_DIR/integrity.json" << EOF
{
  "files": [
    {
      "path": "assets/icon.png",
      "size": $(stat -f%z "$PLUGIN_DIR/assets/icon.png" 2>/dev/null || stat -c%s "$PLUGIN_DIR/assets/icon.png"),
      "sha256": "$ICON_SHA"
    },
    {
      "path": "manifest.json",
      "size": $(stat -f%z "$PLUGIN_DIR/manifest.json" 2>/dev/null || stat -c%s "$PLUGIN_DIR/manifest.json"),
      "sha256": "$MANIFEST_SHA"
    },
    {
      "path": "runtime/plugin.wasm",
      "size": $WASM_SIZE,
      "sha256": "$WASM_SHA"
    },
    {
      "path": "ui/schema.json",
      "size": $(stat -f%z "$PLUGIN_DIR/ui/schema.json" 2>/dev/null || stat -c%s "$PLUGIN_DIR/ui/schema.json"),
      "sha256": "$UI_SHA"
    }
  ]
}
EOF

# 创建 ZIP 包
echo ""
echo "==> 创建插件包..."
cd "$PLUGIN_DIR"
zip -r "$OUTPUT_DIR/115-checkin-plugin.d115p" \
    manifest.json \
    integrity.json \
    signature.json \
    runtime/plugin.wasm \
    ui/schema.json \
    assets/icon.png \
    README.md

PKG_SIZE=$(stat -f%z "$OUTPUT_DIR/115-checkin-plugin.d115p" 2>/dev/null || stat -c%s "$OUTPUT_DIR/115-checkin-plugin.d115p")
echo "插件包大小: ${PKG_SIZE} bytes"

echo ""
echo "=== 构建完成 ==="
echo "输出文件: $OUTPUT_DIR/115-checkin-plugin.d115p"
