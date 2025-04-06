const { contextBridge, ipcRenderer } = require('electron');

// 安全地暴露IPC通信给插件管理器
contextBridge.exposeInMainWorld('pluginAPI', {
  // 获取插件列表
  listPlugins: () => ipcRenderer.invoke('list-plugins'),
  
  // 安装新插件
  installPlugin: () => ipcRenderer.invoke('install-plugin'),
  
  // 启用插件
  enablePlugin: (id) => ipcRenderer.invoke('enable-plugin', id),
  
  // 禁用插件
  disablePlugin: (id) => ipcRenderer.invoke('disable-plugin', id)
}); 