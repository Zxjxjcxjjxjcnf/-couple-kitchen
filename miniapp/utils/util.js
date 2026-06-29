// 格式化时间
const formatTime = (ts) => {
  if (!ts) return '';
  const d = new Date(ts);
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  const h = String(d.getHours()).padStart(2, '0');
  const min = String(d.getMinutes()).padStart(2, '0');
  return `${m}-${day} ${h}:${min}`;
};

// 订单状态中文
const statusLabel = (s) => {
  const map = {
    pending: '待接单',
    cooking: '制作中',
    completed: '已完成',
    cancelled: '已取消',
  };
  return map[s] || s;
};

// Toast 提示
const showToast = (msg, icon = 'none') => {
  wx.showToast({
    title: msg,
    icon,
    duration: 1500,
  });
};

module.exports = { formatTime, statusLabel, showToast };
