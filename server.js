const express = require('express');
const compression = require('compression');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = process.env.PORT || 3000;

// ---- 压缩 ----
app.use(compression());

// ---- 静态文件 ----
app.use(express.static(path.join(__dirname), {
  maxAge: '1h',
  setHeaders: (res, filePath) => {
    if (filePath.endsWith('manifest.json')) {
      res.setHeader('Content-Type', 'application/json');
    }
    res.setHeader('Service-Worker-Allowed', '/');
  },
}));

// ---- 健康检查（Railway 需要） ----
app.get('/health', (req, res) => {
  res.json({ status: 'ok', app: '❤️ 情侣私厨', uptime: process.uptime() });
});

// ---- 所有路由 fallback 到 index.html ----
app.get('*', (req, res) => {
  if (req.path === '/manifest.json') {
    return res.status(404).json({ error: 'manifest not found' });
  }
  if (req.path === '/sw.js') {
    return res.status(404).json({ error: 'sw not found' });
  }
  res.sendFile(path.join(__dirname, 'index.html'));
});

// ---- 启动 ----
app.listen(PORT, '0.0.0.0', () => {
  console.log(`\n  ❤️ 情侣私厨 已启动`);
  console.log(`  ───────────────────────`);
  console.log(`  本地:   http://localhost:${PORT}`);
  console.log(`  线上:   https://你的项目名称.railway.app`);
  console.log(`  健康:   http://localhost:${PORT}/health\n`);
});
