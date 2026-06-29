const api = require('../../utils/api');
const util = require('../../utils/util');
const app = getApp();

Page({
  data: {
    statusTabs: [
      { key: 'pending', label: '待接单' },
      { key: 'cooking', label: '制作中' },
      { key: 'completed', label: '已完成' },
      { key: 'menu', label: '📋 菜单' },
    ],
    chefTab: 'pending',
    orders: [],
    menuItems: [],
    categories: [
      { key: 'meat', label: '肉菜', emoji: '🥩' },
      { key: 'home', label: '家常菜', emoji: '🥬' },
      { key: 'breakfast', label: '早餐', emoji: '🥟' },
    ],

    // 计算后的数据（WXML 不能用 getter）
    filteredOrders: [],
    orderCounts: {},
    currentTabLabel: '',
    catMenuList: [],

    // 添加菜品
    showAddDishModal: false,
    newDish: {
      name: '', category: 'meat', categoryName: '肉菜',
      price: '', emoji: '🍽️', desc: '',
    },
  },

  // 更新计算数据（替代 getter，WXML 只能用 data）
  computeOrders() {
    const { orders, chefTab, statusTabs } = this.data;
    const statusMap = { pending: 'pending', cooking: 'cooking', completed: 'completed' };
    const filtered = orders.filter(o => o.status === statusMap[chefTab]);
    const t = statusTabs.find(t => t.key === chefTab);
    const counts = {};
    statusTabs.forEach(st => {
      if (st.key === 'menu') return;
      counts[st.key] = orders.filter(o => o.status === st.key).length;
    });
    this.setData({
      filteredOrders: filtered,
      currentTabLabel: t ? t.label : '',
      orderCounts: counts,
    });
  },

  onLoad() {
    app.globalData.role = 'chef';
    app.connectWS('chef');
    this.loadOrders();
    this.loadMenu();
    this.computeOrders();
  },

  onShow() {
    this.loadOrders();
    this.computeOrders();
  },

  // 加载订单
  async loadOrders() {
    try {
      const data = await api.get('/api/orders');
      this.setData({ orders: data });
      this.computeOrders();
    } catch(e) {
      console.warn('加载订单失败', e);
    }
  },

  // 加载菜单
  async loadMenu() {
    try {
      const data = await api.get('/api/menu');
      if (data && data.length > 0) {
        this.setData({ menuItems: data });
        this.buildCatMenu();
      }
    } catch(e) {
      console.warn('加载菜单失败', e);
    }
  },

  // 构建分类菜单列表（WXML 不能用 filter）
  buildCatMenu() {
    const { categories, menuItems } = this.data;
    const catMenuList = categories.map(cat => ({
      key: cat.key,
      emoji: cat.emoji,
      label: cat.label,
      count: menuItems.filter(i => i.category === cat.key).length,
      items: menuItems.filter(i => i.category === cat.key),
    }));
    this.setData({ catMenuList });
  },

  // 切换 Tab
  switchTab(e) {
    const key = e.currentTarget.dataset.key;
    this.setData({ chefTab: key });
    this.computeOrders();
    if (key === 'menu') this.loadMenu();
  },

  // 接单
  async acceptOrder(e) {
    const id = e.currentTarget.dataset.id;
    try {
      await api.put(`/api/orders/${id}/status`, { status: 'cooking' });
      this.loadOrders();
      this.computeOrders();
      util.showToast('✅ 已接单', 'none');
    } catch(e) {
      util.showToast('操作失败', 'none');
    }
  },

  // 完成
  async completeOrder(e) {
    const id = e.currentTarget.dataset.id;
    try {
      await api.put(`/api/orders/${id}/status`, { status: 'completed' });
      this.loadOrders();
      this.computeOrders();
      util.showToast('✅ 已完成', 'none');
    } catch(e) {
      util.showToast('操作失败', 'none');
    }
  },

  // 取消订单
  async cancelOrder(e) {
    const id = e.currentTarget.dataset.id;
    try {
      await api.put(`/api/orders/${id}/status`, { status: 'cancelled' });
      this.loadOrders();
      this.computeOrders();
      util.showToast('已取消', 'none');
    } catch(e) {
      util.showToast('操作失败', 'none');
    }
  },

  // 上传菜品图片
  uploadDishImg(e) {
    const id = e.currentTarget.dataset.id;
    wx.chooseImage({
      count: 1,
      sizeType: ['compressed'],
      sourceType: ['album', 'camera'],
      success: async (res) => {
        const filePath = res.tempFilePaths[0];
        try {
          const result = await api.uploadImage(id, filePath);
          this.loadMenu();
          util.showToast('✅ 图片上传成功', 'none');
        } catch(err) {
          util.showToast('上传失败', 'none');
        }
      },
    });
  },

  // 添加菜品
  showAddDish() {
    this.setData({
      showAddDishModal: true,
      newDish: { name: '', category: 'meat', categoryName: '肉菜', price: '', emoji: '🍽️', desc: '' },
    });
  },

  hideAddDish() {
    this.setData({ showAddDishModal: false });
  },

  onCategoryChange(e) {
    const val = e.detail.value;
    const cat = this.data.categories[val];
    this.setData({
      'newDish.category': cat.key,
      'newDish.categoryName': cat.label,
    });
  },

  async addDish() {
    const d = this.data.newDish;
    if (!d.name.trim()) { util.showToast('请输入菜品名', 'none'); return; }
    if (!d.price || d.price <= 0) { util.showToast('请输入有效价格', 'none'); return; }

    try {
      await api.post('/api/menu', {
        name: d.name.trim(),
        category: d.category,
        price: parseFloat(d.price),
        emoji: d.emoji || '🍽️',
        description: d.desc || '',
      });
      this.hideAddDish();
      this.loadMenu();
      util.showToast('✅ 已添加「' + d.name + '」', 'none');
    } catch(e) {
      util.showToast('添加失败', 'none');
    }
  },

  // WebSocket 消息
  onWSMessage(msg) {
    if (msg.type === 'order_new' || msg.type === 'order_update') {
      this.loadOrders();
      this.computeOrders();
      if (msg.type === 'order_new') {
        wx.showToast({ title: '📋 新订单来了！', icon: 'none', duration: 2000 });
        // 自动切换到待接单
        this.setData({ chefTab: 'pending' });
      }
    }
  },

  goHome() {
    wx.navigateBack();
  },

  goGuest() {
    wx.navigateTo({ url: '/pages/guest/guest' });
  },

  noop() {},

  // 需要返回给 WXML 使用的函数
  statusLabel: util.statusLabel,
  formatTime: util.formatTime,
});
