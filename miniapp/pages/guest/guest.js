const api = require('../../utils/api');
const util = require('../../utils/util');
const app = getApp();

// 预置菜单数据（API 加载失败时用）
const MENU_DATA = [];

Page({
  data: {
    // 分类
    categories: [
      { key: 'meat', label: '肉菜', emoji: '🥩' },
      { key: 'home', label: '家常菜', emoji: '🥬' },
      { key: 'breakfast', label: '早餐', emoji: '🥟' },
    ],
    category: 'meat',
    menuItems: [],
    filteredMenu: [],

    // 购物车
    cart: [],
    showCart: false,

    // 详情弹窗
    showDetail: false,
    detailItem: null,
    detailQty: 1,
    detailNote: '',

    // 提交弹窗
    showSubmit: false,
    orderNote: '',
  },

  onLoad() {
    this.loadMenu();
    this.loadCart();
    app.globalData.role = 'guest';
    app.connectWS('guest');
  },

  onShow() {
    this.loadCart();
  },

  // 加载菜单
  async loadMenu() {
    try {
      const data = await api.get('/api/menu');
      if (data && data.length > 0) {
        this.setData({ menuItems: data });
        this.filterMenu();
        return;
      }
    } catch(e) {
      console.warn('加载菜单失败', e);
    }
  },

  // 筛选当前分类
  filterMenu() {
    const { menuItems, category } = this.data;
    const filtered = menuItems.filter(i => i.category === category);
    this.setData({ filteredMenu: filtered });
  },

  // 选择分类
  selectCategory(e) {
    const key = e.currentTarget.dataset.key;
    this.setData({ category: key }, () => this.filterMenu());
  },

  get currentCatLabel() {
    const cat = this.data.categories.find(c => c.key === this.data.category);
    return cat ? cat.emoji + ' ' + cat.label : '';
  },

  // 加载购物车
  loadCart() {
    this.setData({ cart: app.globalData.cart || [] });
  },

  // 保存购物车
  saveCart() {
    app.globalData.cart = this.data.cart;
    app.saveCart();
    this.setData({ cart: this.data.cart });
  },

  // 加入购物车（快捷）
  addToCart(e) {
    const item = e.currentTarget.dataset.item;
    const cart = this.data.cart;
    const exist = cart.find(i => i.id === item.id);
    if (exist) {
      exist.qty++;
    } else {
      cart.push({ ...item, qty: 1, note: '' });
    }
    this.saveCart();
    util.showToast(item.emoji + ' 已加入', 'none');
  },

  // 显示详情
  showDetail(e) {
    const item = e.currentTarget.dataset.item;
    this.setData({
      showDetail: true,
      detailItem: item,
      detailQty: 1,
      detailNote: '',
    });
  },

  hideDetail() {
    this.setData({ showDetail: false });
  },

  detailQtyDec() {
    const q = Math.max(1, this.data.detailQty - 1);
    this.setData({ detailQty: q });
  },

  detailQtyInc() {
    this.setData({ detailQty: this.data.detailQty + 1 });
  },

  addFromDetail() {
    const { detailItem, detailQty, detailNote } = this.data;
    if (!detailItem) return;
    const cart = this.data.cart;
    const exist = cart.find(i => i.id === detailItem.id);
    if (exist) {
      exist.qty += detailQty;
      if (detailNote) exist.note = detailNote;
    } else {
      cart.push({ ...detailItem, qty: detailQty, note: detailNote });
    }
    this.saveCart();
    this.hideDetail();
    util.showToast(detailItem.emoji + ' ×' + detailQty + ' 已加入', 'none');
  },

  // 提交订单
  submitOrder() {
    if (this.data.cart.length === 0) {
      util.showToast('购物车是空的', 'none');
      return;
    }
    this.setData({ showSubmit: true, orderNote: '' });
  },

  hideSubmit() {
    this.setData({ showSubmit: false });
  },

  async confirmOrder() {
    const { cart, orderNote } = this.data;
    if (cart.length === 0) return;

    const payload = {
      items: cart.map(i => ({
        id: i.id, name: i.name, price: i.price,
        qty: i.qty, emoji: i.emoji, note: i.note || '',
      })),
      note: orderNote || '',
    };

    try {
      await api.post('/api/orders', payload);
      this.setData({
        cart: [],
        showSubmit: false,
        orderNote: '',
      });
      this.saveCart();
      util.showToast('🎉 下单成功！', 'none');
    } catch(e) {
      util.showToast('⚠️ 提交失败，请检查网络', 'none');
    }
  },

  // 接收 WebSocket 消息
  onWSMessage(msg) {
    // 订单状态更新时显示提示
    if (msg.type === 'order_update') {
      const order = msg.data;
      if (order.status === 'cooking') {
        util.showToast('👨‍🍳 厨师已接单！', 'none');
      }
      if (order.status === 'completed') {
        util.showToast('🎉 订单已完成！', 'none');
      }
    }
  },

  goHome() {
    wx.navigateBack();
  },

  noop() {},
});
