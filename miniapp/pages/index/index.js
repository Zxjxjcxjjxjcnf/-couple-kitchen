const app = getApp();

Page({
  data: {},

  goGuest() {
    wx.navigateTo({ url: '/pages/guest/guest' });
  },

  goChef() {
    app.globalData.role = 'chef';
    app.connectWS('chef');
    wx.navigateTo({ url: '/pages/chef/chef' });
  },
});
