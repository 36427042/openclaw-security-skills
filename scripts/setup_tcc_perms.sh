#!/bin/bash
# macOS TCC 权限自动授权脚本
# 跑一次后永久生效，不会再弹"node想访问其他App"的窗口
# 使用方式: sudo bash setup_tcc_perms.sh

set -e

echo "=== macOS TCC 权限自动授权 ==="
echo "为 Node.js 添加 AppleEvents 权限..."

# macOS 26+ TCC数据库路径 (系统级)
TCC_DB="/Library/Application Support/com.apple.TCC/TCC.db"

# 更安全的方式: 使用 tccutil 重新设置
# 先停掉 tccd 以释放数据库锁
echo "1. 暂停 tccd 守护进程..."
launchctl bootout system/com.apple.tccd 2>/dev/null || true
sleep 1

# Node.js 路径
NODE_BIN="/opt/homebrew/bin/node"

echo "2. 写入 TCC 权限记录..."
sqlite3 "$TCC_DB" <<SQL
-- 为 node 添加 Automation (AppleEvents) 权限
-- auth_value=2 表示 allowed
INSERT OR REPLACE INTO access (
    service,
    client,
    client_type,
    auth_value,
    auth_reason,
    auth_version,
    csreq,
    policy_id,
    indirect_object_identifier_type,
    indirect_object_identifier,
    flags,
    last_modified
) VALUES (
    'kTCCServiceAppleEvents',
    '$NODE_BIN',
    0,
    2,
    1,
    1,
    NULL,
    NULL,
    'bundled_id',
    'com.apple.systemevents',
    0,
    strftime('%s', 'now')
);
SQL
echo "  ✅ kTCCServiceAppleEvents 已授权"

# 也添加 Accessibility 权限以防需要
sqlite3 "$TCC_DB" <<SQL
INSERT OR REPLACE INTO access (
    service, client, client_type, auth_value, auth_reason, auth_version,
    csreq, policy_id, indirect_object_identifier_type,
    indirect_object_identifier, flags, last_modified
) VALUES (
    'kTCCServiceAccessibility',
    '$NODE_BIN',
    0,
    2,
    1,
    1,
    NULL,
    NULL,
    'bundled_id',
    'com.apple.systemevents',
    0,
    strftime('%s', 'now')
);
SQL
echo "  ✅ kTCCServiceAccessibility 已授权"

echo "3. 重启 tccd..."
launchctl bootstrap system /System/Library/LaunchDaemons/com.apple.tccd.plist 2>/dev/null || true
sleep 1

echo ""
echo "=== ✅ TCC 权限设置完成 ==="
echo "以后不会再弹出权限许可对话框"
echo ""
echo "测试方法: osascript -e 'tell application \"Finder\" to get name of every window'"
