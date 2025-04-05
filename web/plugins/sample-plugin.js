// OpenKimi 示例插件
// 这个插件展示了如何创建一个简单的OpenKimi插件

// 定义插件信息和功能
const samplePlugin = {
    // 插件基本信息
    id: 'sample-plugin',
    name: '示例插件',
    version: '1.0.0',
    description: '这是一个示例插件，展示了OpenKimi插件系统的基本功能',
    author: '示例作者',
    enabled: true, // 默认启用

    // 插件初始化函数，在插件注册时调用
    init: function(app) {
        console.log('示例插件已初始化!');
        
        // 可以在这里访问app实例或执行其他初始化操作
        // app是Vue应用实例
    },

    // 定义插件的钩子函数
    hooks: {
        // 消息发送前处理
        beforeSendMessage: function(message) {
            console.log('示例插件处理消息:', message);
            
            // 示例：为消息添加前缀标记
            if (!message.startsWith("[插件测试]") && Math.random() > 0.5) {
                return `[插件测试] ${message}`;
            }
            return message;
        },
        
        // 收到回复后处理
        afterReceiveMessage: function(response) {
            console.log('示例插件处理回复:', response);
            
            // 示例：为回复添加插件签名
            if (!response.includes("--- 由示例插件处理")) {
                return `${response}\n\n--- 由示例插件处理`;
            }
            return response;
        },
        
        // 搜索结果处理
        onSearchResults: function(results) {
            console.log('示例插件处理搜索结果');
            // 这里可以处理搜索结果
            return results;
        },
        
        // 文件上传处理
        onFileUpload: function(fileInfo) {
            console.log('示例插件处理文件上传:', fileInfo);
            // 这里可以处理文件上传事件
            return fileInfo;
        }
    },

    // 插件可以定义自己的方法
    customMethods: {
        doSomething: function() {
            alert('示例插件执行了自定义操作!');
        }
    }
};

// 将插件对象设置为全局变量，以便插件系统加载
// 这里使用了默认的全局变量名 _latestLoadedPlugin
window._latestLoadedPlugin = samplePlugin; 