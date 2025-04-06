// 预加载脚本在渲染进程加载之前执行
const { contextBridge, ipcRenderer } = require('electron');

// 安全地暴露API给渲染进程
contextBridge.exposeInMainWorld('electronAPI', {
  // 导出聊天历史
  exportHistory: (callback) => {
    ipcRenderer.on('export-history', (event, filePath) => {
      callback(filePath);
    });
  },
  
  // 获取平台信息
  getPlatformInfo: () => {
    return {
      platform: process.platform,
      version: process.getSystemVersion(),
      arch: process.arch
    };
  }
});

// 在DOM加载完成后执行
window.addEventListener('DOMContentLoaded', () => {
  console.log('Kimi客户端已加载');
  
  // 这里可以向页面注入一些增强功能
  // 例如：添加桌面客户端专属的DOM元素或样式
  
  // 注入客户端信息
  const injectClientInfo = () => {
    // 创建客户端标识元素
    const clientBadge = document.createElement('div');
    clientBadge.className = 'kimi-electron-badge';
    clientBadge.style.cssText = `
      position: fixed;
      bottom: 10px;
      right: 10px;
      background: rgba(0, 0, 0, 0.6);
      color: white;
      padding: 4px 8px;
      border-radius: 4px;
      font-size: 12px;
      z-index: 9999;
    `;
    clientBadge.textContent = `Kimi桌面客户端 v${require('./package.json').version}`;
    document.body.appendChild(clientBadge);
  };
  
  // 尝试注入客户端信息，如果DOM还没完全加载则延迟执行
  setTimeout(() => {
    if (document.body) {
      injectClientInfo();
    } else {
      // 如果body还不存在，则等待更长时间
      setTimeout(injectClientInfo, 1000);
    }
  }, 500);
}); 