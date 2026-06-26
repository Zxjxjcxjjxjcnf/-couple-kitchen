#!/bin/bash
# Railway 启动脚本（Procfile 会调用此脚本）
set -e
exec python -c "
import os, uvicorn
port = int(os.getenv('PORT', '8000'))
print(f'[启动] 端口: {port}')
uvicorn.run('backend.main:app', host='0.0.0.0', port=port, proxy_headers=True, forwarded_allow_ips='*')
"
