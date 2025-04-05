// OpenKimi 插件系统
// 这个文件实现了一个简单的插件系统，允许动态加载和注册插件

class PluginSystem {
    constructor(app) {
        this.app = app; // Vue 应用实例的引用
        this.plugins = {}; // 存储已加载的插件
        this.hooks = {
            // 定义各种钩子点
            'beforeSendMessage': [],
            'afterReceiveMessage': [],
            'onSearchResults': [],
            'onFileUpload': [],
            'onStartChat': []
        };
    }

    // 注册一个插件
    register(pluginInfo) {
        if (!pluginInfo.id || !pluginInfo.name) {
            console.error('插件缺少必要的 id 或 name 属性');
            return false;
        }

        if (this.plugins[pluginInfo.id]) {
            console.warn(`插件 ${pluginInfo.id} 已经注册，将被覆盖`);
        }

        // 存储插件信息
        this.plugins[pluginInfo.id] = {
            ...pluginInfo,
            enabled: pluginInfo.enabled || false,
            loaded: true
        };

        console.log(`插件 "${pluginInfo.name}" (${pluginInfo.id}) 已注册`);
        
        // 如果插件有初始化函数，则调用它
        if (typeof pluginInfo.init === 'function') {
            try {
                pluginInfo.init(this.app);
            } catch (error) {
                console.error(`初始化插件 ${pluginInfo.id} 时出错:`, error);
            }
        }

        // 如果插件已启用，注册其钩子
        if (pluginInfo.enabled && pluginInfo.hooks) {
            this.registerHooks(pluginInfo.id, pluginInfo.hooks);
        }

        return true;
    }

    // 从URL加载一个插件
    async loadFromUrl(url, options = {}) {
        try {
            // 创建一个script元素来加载JavaScript
            const script = document.createElement('script');
            script.type = 'text/javascript';
            script.src = url;
            
            return new Promise((resolve, reject) => {
                script.onload = () => {
                    console.log(`从 ${url} 加载插件脚本成功`);
                    
                    // 假设脚本执行后会设置一个全局变量，其名称由options.globalVar指定
                    // 如果没有指定，则使用默认的'_latestLoadedPlugin'
                    const globalVarName = options.globalVar || '_latestLoadedPlugin';
                    
                    if (window[globalVarName]) {
                        // 注册插件
                        const result = this.register(window[globalVarName]);
                        
                        // 清除全局变量
                        if (!options.keepGlobal) {
                            delete window[globalVarName];
                        }
                        
                        resolve(result);
                    } else {
                        reject(new Error('加载的插件没有通过预期的全局变量公开自己'));
                    }
                };
                
                script.onerror = () => {
                    reject(new Error(`从 ${url} 加载插件脚本失败`));
                };
                
                // 添加到文档以开始加载
                document.head.appendChild(script);
            });
        } catch (error) {
            console.error('加载插件时出错:', error);
            return false;
        }
    }

    // 启用插件
    enable(pluginId) {
        const plugin = this.plugins[pluginId];
        if (!plugin) {
            console.error(`未找到插件 ${pluginId}`);
            return false;
        }

        plugin.enabled = true;
        
        // 注册钩子
        if (plugin.hooks) {
            this.registerHooks(pluginId, plugin.hooks);
        }
        
        console.log(`插件 "${plugin.name}" 已启用`);
        return true;
    }

    // 禁用插件
    disable(pluginId) {
        const plugin = this.plugins[pluginId];
        if (!plugin) {
            console.error(`未找到插件 ${pluginId}`);
            return false;
        }

        plugin.enabled = false;
        
        // 移除钩子
        this.unregisterHooks(pluginId);
        
        console.log(`插件 "${plugin.name}" 已禁用`);
        return true;
    }

    // 注册插件的钩子
    registerHooks(pluginId, hooks) {
        for (const [hookName, hookFunc] of Object.entries(hooks)) {
            if (this.hooks[hookName] && typeof hookFunc === 'function') {
                this.hooks[hookName].push({
                    pluginId,
                    hookFunc
                });
                console.log(`插件 ${pluginId} 注册了钩子: ${hookName}`);
            }
        }
    }

    // 注销插件的钩子
    unregisterHooks(pluginId) {
        for (const hookName in this.hooks) {
            this.hooks[hookName] = this.hooks[hookName].filter(hook => hook.pluginId !== pluginId);
        }
        console.log(`插件 ${pluginId} 的所有钩子已移除`);
    }

    // 触发一个钩子，执行所有注册到该钩子的函数
    async triggerHook(hookName, ...args) {
        if (!this.hooks[hookName]) {
            console.warn(`未定义的钩子: ${hookName}`);
            return args;
        }

        let result = args;
        
        // 按顺序执行钩子函数，每个钩子可以修改参数
        for (const hook of this.hooks[hookName]) {
            try {
                // 每个钩子函数接收上一个钩子的输出作为输入
                const hookResult = await hook.hookFunc(...result);
                if (hookResult !== undefined) {
                    result = Array.isArray(hookResult) ? hookResult : [hookResult];
                }
            } catch (error) {
                console.error(`插件 ${hook.pluginId} 的钩子 ${hookName} 执行出错:`, error);
            }
        }
        
        return result.length <= 1 ? result[0] : result;
    }

    // 获取所有已注册的插件
    getAllPlugins() {
        return Object.values(this.plugins);
    }

    // 获取所有启用的插件
    getEnabledPlugins() {
        return Object.values(this.plugins).filter(plugin => plugin.enabled);
    }
}

// 导出全局插件系统实例
window.PluginSystem = PluginSystem; 