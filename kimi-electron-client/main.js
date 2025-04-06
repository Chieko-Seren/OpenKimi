const { app, BrowserWindow, Menu, ipcMain, dialog } = require('electron');
const path = require('path');
const fs = require('fs');

// 保持对窗口对象的全局引用，避免JavaScript对象被垃圾回收时窗口关闭
let mainWindow;
let pluginWindow;

// 插件存储路径
const pluginsPath = path.join(app.getPath('userData'), 'plugins');

// 确保插件目录存在
function ensurePluginsDirectory() {
  if (!fs.existsSync(pluginsPath)) {
    fs.mkdirSync(pluginsPath, { recursive: true });
  }
}

function createWindow() {
  // 创建浏览器窗口
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false, // 出于安全考虑，禁用Node集成
      contextIsolation: true  // 启用上下文隔离
    },
    icon: path.join(__dirname, 'assets/icon.png') // 应用图标
  });

  // 加载OpenKimi网站
  mainWindow.loadURL('https://chieko-seren.github.io/OpenKimi/');

  // 创建应用菜单
  createMenu();

  // 当窗口关闭时触发
  mainWindow.on('closed', function() {
    mainWindow = null;
  });
}

// 创建应用菜单
function createMenu() {
  const template = [
    {
      label: '文件',
      submenu: [
        {
          label: '导出聊天记录',
          click: async () => {
            const { filePath } = await dialog.showSaveDialog({
              title: '导出聊天记录',
              defaultPath: 'kimi-chat-history.json',
              filters: [{ name: 'JSON文件', extensions: ['json'] }]
            });
            
            if (filePath) {
              mainWindow.webContents.send('export-history', filePath);
            }
          }
        },
        { type: 'separator' },
        { label: '退出', role: 'quit' }
      ]
    },
    {
      label: '查看',
      submenu: [
        { role: 'reload' },
        { role: 'toggleDevTools' },
        { type: 'separator' },
        { role: 'togglefullscreen' }
      ]
    },
    {
      label: '插件',
      submenu: [
        {
          label: '管理本地插件',
          click: () => {
            // 打开本地插件管理窗口
            createPluginManager();
          }
        }
      ]
    }
  ];
  
  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

// 本地插件管理窗口
function createPluginManager() {
  // 如果已经打开则聚焦而不是创建新窗口
  if (pluginWindow) {
    pluginWindow.focus();
    return;
  }

  pluginWindow = new BrowserWindow({
    width: 800,
    height: 600,
    parent: mainWindow,
    modal: false,
    webPreferences: {
      preload: path.join(__dirname, 'plugin-preload.js'),
      nodeIntegration: false,
      contextIsolation: true
    },
    title: 'Kimi 插件管理器'
  });
  
  pluginWindow.loadFile(path.join(__dirname, 'renderer/plugin-manager.html'));
  
  // 窗口关闭时清除引用
  pluginWindow.on('closed', () => {
    pluginWindow = null;
  });
}

// 设置IPC通信
function setupIPC() {
  // 列出所有本地插件
  ipcMain.handle('list-plugins', async () => {
    ensurePluginsDirectory();
    
    try {
      const files = fs.readdirSync(pluginsPath);
      const plugins = [];
      
      for (const file of files) {
        if (file.endsWith('.js')) {
          const fullPath = path.join(pluginsPath, file);
          // 读取文件内容获取插件信息
          // 实际实现中可能需要更复杂的解析逻辑
          const content = fs.readFileSync(fullPath, 'utf8');
          // 简单示例：从注释或特定格式中提取插件信息
          const nameMatch = content.match(/name:\s*['"]([^'"]+)['"]/);
          const idMatch = content.match(/id:\s*['"]([^'"]+)['"]/);
          const descMatch = content.match(/description:\s*['"]([^'"]+)['"]/);
          const enabledMatch = content.match(/enabled:\s*(true|false)/);
          
          plugins.push({
            id: idMatch ? idMatch[1] : file.replace('.js', ''),
            name: nameMatch ? nameMatch[1] : file,
            description: descMatch ? descMatch[1] : '本地插件',
            enabled: enabledMatch ? enabledMatch[1] === 'true' : false,
            path: fullPath
          });
        }
      }
      
      return plugins;
    } catch (err) {
      console.error('获取插件列表失败:', err);
      return [];
    }
  });
  
  // 安装新插件
  ipcMain.handle('install-plugin', async () => {
    ensurePluginsDirectory();
    
    const { canceled, filePaths } = await dialog.showOpenDialog({
      title: '选择插件文件',
      filters: [{ name: 'JavaScript文件', extensions: ['js'] }],
      properties: ['openFile']
    });
    
    if (canceled || filePaths.length === 0) {
      return { success: false, error: '未选择文件' };
    }
    
    try {
      const sourcePath = filePaths[0];
      const fileName = path.basename(sourcePath);
      const targetPath = path.join(pluginsPath, fileName);
      
      // 复制插件文件到应用数据目录
      fs.copyFileSync(sourcePath, targetPath);
      
      // 读取插件内容获取基本信息
      const content = fs.readFileSync(targetPath, 'utf8');
      const nameMatch = content.match(/name:\s*['"]([^'"]+)['"]/);
      
      return { 
        success: true, 
        name: nameMatch ? nameMatch[1] : fileName,
        path: targetPath
      };
    } catch (err) {
      console.error('安装插件失败:', err);
      return { success: false, error: err.message };
    }
  });
  
  // 启用插件
  ipcMain.handle('enable-plugin', async (event, id) => {
    ensurePluginsDirectory();
    
    try {
      // 这里应该实现实际的启用逻辑
      // 可能涉及修改插件文件或配置文件
      console.log(`启用插件: ${id}`);
      return { success: true };
    } catch (err) {
      console.error(`启用插件 ${id} 失败:`, err);
      return { success: false, error: err.message };
    }
  });
  
  // 禁用插件
  ipcMain.handle('disable-plugin', async (event, id) => {
    ensurePluginsDirectory();
    
    try {
      // 这里应该实现实际的禁用逻辑
      console.log(`禁用插件: ${id}`);
      return { success: true };
    } catch (err) {
      console.error(`禁用插件 ${id} 失败:`, err);
      return { success: false, error: err.message };
    }
  });
}

// 应用准备就绪时创建窗口
app.whenReady().then(() => {
  setupIPC();
  ensurePluginsDirectory();
  createWindow();
  
  // 在macOS上，点击dock图标时没有已打开的窗口则重新创建一个窗口
  app.on('activate', function() {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

// 所有窗口关闭时退出应用（Windows & Linux）
app.on('window-all-closed', function() {
  if (process.platform !== 'darwin') app.quit();
}); 