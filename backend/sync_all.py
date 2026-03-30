#!/usr/bin/env python3
"""同步所有数据的脚本"""

from database import get_db, init_db
from request_sync import sync_request_logs

# 初始化数据库
init_db()

# 获取数据库会话
db = next(get_db())

print('🔄 开始同步所有数据...')

# 同步请求日志（回溯24小时）
print('1️⃣ 同步请求日志...')
try:
    request_count = sync_request_logs(db, lookback_hours=24)
    db.commit()
    print(f'   ✅ 请求日志同步完成：{request_count} 条')
except Exception as e:
    print(f'   ❌ 请求日志同步失败：{e}')

db.close()
print('✅ 数据同步完成！')
