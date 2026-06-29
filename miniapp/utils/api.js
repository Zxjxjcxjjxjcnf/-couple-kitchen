// 获取 API 基础地址
const getBase = () => {
  const app = getApp();
  return app.globalData.API_BASE;
};

// GET 请求
const get = (path) => {
  return new Promise((resolve, reject) => {
    wx.request({
      url: getBase() + path,
      method: 'GET',
      success: (res) => resolve(res.data),
      fail: reject,
    });
  });
};

// POST 请求
const post = (path, data) => {
  return new Promise((resolve, reject) => {
    wx.request({
      url: getBase() + path,
      method: 'POST',
      data,
      header: { 'Content-Type': 'application/json' },
      success: (res) => resolve(res.data),
      fail: reject,
    });
  });
};

// PUT 请求
const put = (path, data) => {
  return new Promise((resolve, reject) => {
    wx.request({
      url: getBase() + path,
      method: 'PUT',
      data,
      header: { 'Content-Type': 'application/json' },
      success: (res) => resolve(res.data),
      fail: reject,
    });
  });
};

// 上传图片
const uploadImage = (itemId, filePath) => {
  return new Promise((resolve, reject) => {
    wx.uploadFile({
      url: getBase() + '/api/menu/' + itemId + '/image',
      filePath,
      name: 'file',
      success: (res) => {
        try { resolve(JSON.parse(res.data)); }
        catch(e) { resolve(res.data); }
      },
      fail: reject,
    });
  });
};

module.exports = { get, post, put, uploadImage };
