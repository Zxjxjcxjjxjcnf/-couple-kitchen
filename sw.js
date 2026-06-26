/* ===========================================================
   ❤️ 情侣私厨 — Service Worker
   - 缓存静态资源（离线可用）
   - 接收 Firebase Cloud Messaging 推送通知
   - 点击通知跳转到对应页面
   =========================================================== */

const CACHE_NAME = 'couple-kitchen-v2';
const ASSETS = [
  'index.html',
  'manifest.json',
];

// ---- 安装：预缓存核心资源 ----
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS).catch(() => {
        // 单个资源失败不影响安装
        console.warn('[SW] 部分资源缓存失败');
      });
    }).then(() => self.skipWaiting())
  );
});

// ---- 激活：清理旧缓存 ----
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))
      );
    }).then(() => self.clients.claim())
  );
});

// ---- 拦截请求：缓存优先，网络兜底 ----
self.addEventListener('fetch', (event) => {
  // 只缓存同源 GET 请求
  if (event.request.method !== 'GET') return;
  const url = new URL(event.request.url);
  if (url.origin !== self.location.origin) return;

  event.respondWith(
    caches.match(event.request).then((cached) => {
      return cached || fetch(event.request).then((response) => {
        // 成功响应才缓存
        if (response.ok && response.type === 'basic') {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
        }
        return response;
      }).catch(() => {
        // 离线时返回缓存首页
        return caches.match('index.html');
      });
    })
  );
});

// ---- Firebase Cloud Messaging 推送通知 ----
// 当 Firebase 在后台收到推送消息时，此事件被触发
self.addEventListener('push', (event) => {
  if (!event.data) return;

  try {
    const payload = event.data.json();
    const data = payload.data || payload.notification || {};
    const title = data.title || '❤️ 情侣私厨';
    const body = data.body || '你有新的消息～';
    const icon = data.icon || '/android-icon-192x192.png';
    const badge = '/badge-icon.png';
    const tag = data.tag || 'order-update';
    const role = data.role || '';
    const orderId = data.orderId || '';

    // 构造通知点击后的跳转 URL
    let clickUrl = 'index.html';
    if (role === 'chef') clickUrl = 'index.html?role=chef&focus=orders';
    else if (role === 'guest' && orderId) clickUrl = `index.html?role=guest&orderId=${orderId}`;

    event.waitUntil(
      self.registration.showNotification(title, {
        body,
        icon,
        badge,
        tag,
        data: { clickUrl, role, orderId },
        vibrate: [200, 100, 200],
        requireInteraction: true,
        actions: [
          { action: 'open', title: '查看' },
          { action: 'close', title: '关闭' },
        ],
      })
    );
  } catch (e) {
    console.warn('[SW] 推送解析失败:', e);
  }
});

// ---- 点击通知 ----
self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  const clickUrl = event.notification.data?.clickUrl || 'index.html';
  const role = event.notification.data?.role || '';

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
      // 如果已有打开的页面，聚焦并导航
      for (const client of clientList) {
        if (client.url.includes('index.html') && 'navigate' in client) {
          client.focus();
          client.navigate(clickUrl);
          return;
        }
      }
      // 否则打开新窗口
      if (clients.openWindow) {
        return clients.openWindow(clickUrl);
      }
    })
  );
});
