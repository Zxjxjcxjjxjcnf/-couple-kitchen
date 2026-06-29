// app.js
App({
  globalData: {
    // FastAPI 后端地址（部署后的 HTTPS 链接）
    // 本地测试用：http://localhost:8000
    // 生产环境换成你的 Railway 域名
    API_BASE: 'https://your-railway-app.up.railway.app',
    
    // 当前 WebSocket 连接
    ws: null,
    
    // 购物车
    cart: [],
    
    // 菜单缓存
    menuCache: [],
    
    // 用户角色（guest / chef）
    role: 'guest',
  },

  onLaunch() {
    // 加载购物车缓存
    try {
      const cart = wx.getStorageSync('cart');
      if (cart) this.globalData.cart = cart;
    } catch(e) {}
  },

  // 保存购物车
  saveCart() {
    wx.setStorageSync('cart', this.globalData.cart);
  },

  // 连接 WebSocket
  connectWS(role) {
    if (this.globalData.ws) {
      this.globalData.ws.close();
    }
    const base = this.globalData.API_BASE.replace(/^http/, 'ws');
    const url = `${base}/api/orders/ws`;
    
    try {
      const ws = wx.connectSocket({ url });
      this.globalData.ws = ws;
      
      ws.onOpen(() => {
        ws.send({ data: JSON.stringify({ type: 'subscribe', role }) });
        console.log('[WS] 已连接');
      });
      
      ws.onMessage((res) => {
        try {
          const msg = JSON.parse(res.data);
          this.handleWSMessage(msg);
        } catch(e) {}
      });
      
      ws.onClose(() => {
        console.log('[WS] 断开');
        // 5秒后重连
        setTimeout(() => this.connectWS(role), 5000);
      });
    } catch(e) {
      console.warn('[WS] 连接失败', e);
    }
  },

  handleWSMessage(msg) {
    // 广播给当前页面
    const pages = getCurrentPages();
    const page = pages[pages.length - 1];
    if (page && page.onWSMessage) {
      page.onWSMessage(msg);
    }
  },
});
