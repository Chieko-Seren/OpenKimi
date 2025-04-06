document.addEventListener('DOMContentLoaded', async () => {
  const pluginList = document.getElementById('pluginList');
  const installButton = document.getElementById('installPlugin');

  // 刷新插件列表的函数
  const refreshPluginList = async () => {
    pluginList.innerHTML = '<p>加载插件中...</p>';
    try {
      const plugins = await window.pluginAPI.listPlugins();
      pluginList.innerHTML = ''; // 清空旧列表
      
      if (plugins.length === 0) {
        pluginList.innerHTML = '<p>没有安装本地插件</p>';
        return;
      }
      
      plugins.forEach(plugin => {
        const item = document.createElement('div');
        item.className = 'plugin-item';
        item.innerHTML = `
          <div class="plugin-info">
            <h3>${plugin.name}</h3>
            <p>${plugin.description || '无描述'}</p>
            <small>ID: ${plugin.id}</small>
          </div>
          <div class="plugin-actions">
            <button class="toggle-btn ${plugin.enabled ? 'enabled' : 'disabled'}" 
                    data-id="${plugin.id}" 
                    data-enabled="${plugin.enabled}">
              ${plugin.enabled ? '禁用' : '启用'}
            </button>
          </div>
        `;
        pluginList.appendChild(item);
      });
      
      // 添加切换按钮的事件监听器
      document.querySelectorAll('.toggle-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
          const id = btn.dataset.id;
          const enabled = btn.dataset.enabled === 'true';
          
          try {
            if (enabled) {
              await window.pluginAPI.disablePlugin(id);
            } else {
              await window.pluginAPI.enablePlugin(id);
            }
            await refreshPluginList(); // 成功后刷新列表
          } catch (error) {
            console.error('切换插件状态失败:', error);
            alert('切换插件状态失败');
          }
        });
      });
      
    } catch (error) {
      console.error('获取插件列表失败:', error);
      pluginList.innerHTML = '<p>获取插件列表失败</p>';
    }
  };

  // 安装插件按钮的事件监听器
  installButton.addEventListener('click', async () => {
    installButton.disabled = true;
    installButton.textContent = '安装中...';
    try {
      const result = await window.pluginAPI.installPlugin();
      if (result.success) {
        alert(`插件安装成功: ${result.name}`);
        await refreshPluginList(); // 成功后刷新列表
      } else {
        alert(`插件安装失败: ${result.error}`);
      }
    } catch (error) {
      console.error('安装插件失败:', error);
      alert('安装插件失败');
    } finally {
      installButton.disabled = false;
      installButton.textContent = '安装本地插件';
    }
  });

  // 初始加载插件列表
  await refreshPluginList();
}); 