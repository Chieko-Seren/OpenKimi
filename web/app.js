const { createApp, ref, onMounted, nextTick } = Vue;

const App = {
    setup() {
        const history = ref([]); // Stores chat messages {id, role, content}
        const userInput = ref('');
        const isLoading = ref(false);
        const apiUrl = ref(localStorage.getItem('openKimiApiUrl') || 'http://127.0.0.1:8000'); // Default API URL
        const apiStatus = ref('未知');
        const chatHistory = ref(null); // Ref for the chat history div
        const chatStarted = ref(false); // New state variable
        const suggestions = ref([]); // New state for suggestions
        const suggestionsLoading = ref(true); // State for loading suggestions
        const fileInput = ref(null); // Ref for file input element
        const uploadedFiles = ref([]); // 存储已上传的文件
        const isUploading = ref(false); // 文件上传中状态
        const useCoT = ref(false); // 是否使用CoT(Chain of Thought)长思考
        const useWebSearch = ref(false); // 是否使用网络搜索
        const isSearching = ref(false); // 网络搜索中状态
        const searchResults = ref([]); // 搜索结果
        const sidebarOpen = ref(false); // 侧边菜单打开状态
        const activeTab = ref('chat'); // 当前激活的侧边栏标签

        // --- API Interaction ---
        const checkApiStatus = async () => {
            apiStatus.value = '检查中...';
            try {
                console.log(`正在检查API状态: ${apiUrl.value}/health`);
                const response = await fetch(`${apiUrl.value}/health`);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const data = await response.json();
                console.log('API 状态响应:', data);
                
                if (data.status === 'ok' && data.engine_initialized) {
                    apiStatus.value = `正常 (${data.model_name})`;
                } else {
                    apiStatus.value = `错误: ${data.detail || '引擎未初始化'}`;
                    console.error('API引擎初始化失败:', data);
                }
                localStorage.setItem('openKimiApiUrl', apiUrl.value);
            } catch (error) {
                console.error('API Status Check Error:', error);
                apiStatus.value = `连接失败 (${error.message})`; // 更详细的错误信息
            }
        };

        const fetchSuggestions = async () => {
            suggestionsLoading.value = true;
            suggestions.value = []; // Clear previous suggestions
            try {
                const response = await fetch(`${apiUrl.value}/api/suggestions`);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const data = await response.json();
                if (Array.isArray(data)) {
                    suggestions.value = data;
                } else {
                     console.error("Fetched suggestions data is not an array:", data);
                     // Keep suggestions empty or use defaults handled by API?
                }
            } catch (error) {
                console.error('Error fetching suggestions:', error);
                // Keep suggestions empty, API provides defaults on error
            } finally {
                suggestionsLoading.value = false;
            }
        };

        // 处理文件上传
        const handleFileUpload = async (event) => {
            const files = event.target.files;
            if (!files || files.length === 0) return;
            
            isUploading.value = true;
            
            try {
                for (let i = 0; i < files.length; i++) {
                    const file = files[i];
                    // 检查文件类型
                    const fileType = file.type;
                    const fileName = file.name;
                    const fileExtension = fileName.split('.').pop().toLowerCase();
                    
                    // 检查文件类型和扩展名
                    const allowedTypes = [
                        'application/pdf', 
                        'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 
                        'text/plain',
                        'application/msword'
                    ];
                    const allowedExtensions = ['pdf', 'docx', 'txt', 'doc'];
                    
                    if (!allowedTypes.includes(fileType) && !allowedExtensions.includes(fileExtension)) {
                        throw new Error(`不支持的文件类型: ${fileName}。请上传 PDF、DOCX 或 TXT 文件。`);
                    }
                    
                    // 创建FormData来上传文件
                    const formData = new FormData();
                    formData.append('file', file);
                    
                    const response = await fetch(`${apiUrl.value}/v1/files/upload`, {
                        method: 'POST',
                        body: formData
                    });
                    
                    if (!response.ok) {
                        const errorData = await response.json().catch(() => ({ detail: '上传失败' }));
                        throw new Error(`文件上传失败: ${errorData.detail || response.statusText}`);
                    }
                    
                    const data = await response.json();
                    console.log("File upload response:", data);
                    
                    // 添加到已上传文件列表
                    uploadedFiles.value.push({
                        id: data.file_id || Date.now(),
                        name: fileName,
                        type: fileType,
                        status: '已上传'
                    });
                    
                    // 将上传成功的消息添加到聊天历史
                    if (!chatStarted.value) {
                        chatStarted.value = true;
                        await nextTick();
                    }
                    
                    // 添加系统消息，显示文件已上传
                    history.value.push({
                        id: Date.now(),
                        role: 'system',
                        content: `文件 "${fileName}" 已上传成功，正在分析...`
                    });
                    
                    // 系统消息处理文件
                    await ingestFile(data.file_id, fileName);
                }
            } catch (error) {
                console.error('File upload error:', error);
                history.value.push({
                    id: Date.now(),
                    role: 'system',
                    content: `文件上传错误: ${error.message}`
                });
            } finally {
                isUploading.value = false;
                // 清空文件选择器，允许重新选择相同文件
                if (fileInput.value) {
                    fileInput.value.value = '';
                }
                scrollToBottom();
            }
        };
        
        // 处理文件摄入
        const ingestFile = async (fileId, fileName) => {
            try {
                const response = await fetch(`${apiUrl.value}/v1/files/ingest`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        file_id: fileId
                    })
                });
                
                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({ detail: '处理失败' }));
                    throw new Error(`文件处理失败: ${errorData.detail || response.statusText}`);
                }
                
                const data = await response.json();
                
                // 更新文件状态
                const fileIndex = uploadedFiles.value.findIndex(f => f.id === fileId);
                if (fileIndex !== -1) {
                    uploadedFiles.value[fileIndex].status = '已处理';
                }
                
                // 添加助手消息，表示文件已处理
                history.value.push({
                    id: Date.now(),
                    role: 'assistant',
                    content: `我已成功处理文件 "${fileName}"。您可以开始提问关于该文件的内容。`
                });
                
                scrollToBottom();
            } catch (error) {
                console.error('File ingest error:', error);
                history.value.push({
                    id: Date.now(),
                    role: 'assistant',
                    content: `文件处理错误: ${error.message}`
                });
                scrollToBottom();
            }
        };
        
        // 触发文件上传对话框
        const triggerFileUpload = () => {
            if (fileInput.value) {
                fileInput.value.click();
            }
        };

        // 切换长思考模式
        const toggleCoT = () => {
            useCoT.value = !useCoT.value;
        };

        // 切换网络搜索模式
        const toggleWebSearch = () => {
            useWebSearch.value = !useWebSearch.value;
        };

        // 更新执行网页搜索功能
        const performWebSearch = async () => {
            if (!userInput.value.trim() || isSearching.value) {
                return;
            }

            try {
                isSearching.value = true;
                searchResults.value = [];
                const searchQuery = userInput.value.trim();
                
                // 更新聊天历史，显示搜索中消息
                history.value.push({
                    role: "user",
                    content: `搜索: ${searchQuery}`
                });
                
                history.value.push({
                    role: "assistant",
                    content: `<div class="search-message">正在搜索 "${searchQuery}"<span class="thinking-dots"><span>.</span><span>.</span><span>.</span></span></div>`
                });
                
                // 滚动到底部
                setTimeout(scrollToBottom, 100);
                
                const response = await fetch(`${apiUrl.value}/v1/web_search`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        query: searchQuery
                    }),
                });
                
                if (!response.ok) {
                    throw new Error(`搜索请求失败: ${response.status}`);
                }
                
                const searchData = await response.json();
                
                // 更新搜索结果
                searchResults.value = searchData.results;
                
                // 更新最后一条消息，替换"搜索中"为实际结果
                if (history.value.length > 0) {
                    // 删除"搜索中"的消息
                    history.value.pop();
                    
                    // 添加搜索结果消息
                    let searchResultsHTML = `<div class="search-message">搜索 "${searchQuery}" 的结果:</div><div class="search-results">`;
                    
                    searchData.results.forEach(result => {
                        searchResultsHTML += `
                            <div class="search-result-item">
                                <div class="search-result-title"><a href="${result.link}" target="_blank">${result.title}</a></div>
                                <div class="search-result-link">${result.link}</div>
                                <div class="search-result-snippet">${result.snippet}</div>
                            </div>
                        `;
                    });
                    
                    searchResultsHTML += '</div>';
                    
                    history.value.push({
                        role: "assistant",
                        content: searchResultsHTML
                    });
                }
                
                // 清空输入框，为用户提问准备
                userInput.value = '';
                
                setTimeout(scrollToBottom, 100);
            } catch (error) {
                console.error('搜索出错:', error);
                // 更新最后一条消息，显示错误
                if (history.value.length > 0 && history.value[history.value.length - 1].role === 'assistant') {
                    history.value.pop(); // 删除"搜索中"消息
                    history.value.push({
                        role: "assistant",
                        content: `<div class="search-message error">搜索失败: ${error.message}</div>`
                    });
                }
            } finally {
                isSearching.value = false;
                setTimeout(scrollToBottom, 100);
            }
        };

        // 只执行网络搜索，不发送消息
        const searchOnlyWeb = async () => {
            if (!userInput.value.trim() || isSearching.value) {
                return;
            }

            try {
                isSearching.value = true;
                searchResults.value = [];
                
                // 如果还没有开始聊天，先开始
                if (!chatStarted.value) {
                    chatStarted.value = true;
                }
                
                await performWebSearch();
                
                // 不清空输入框，方便用户基于搜索结果调整问题
            } catch (error) {
                console.error('独立搜索出错:', error);
            } finally {
                isSearching.value = false;
            }
        };

        // 切换侧边栏
        const toggleSidebar = () => {
            sidebarOpen.value = !sidebarOpen.value;
        };

        // 设置活动标签
        const setActiveTab = (tab) => {
            activeTab.value = tab;
        };

        // Combined function for sending message or starting chat
        const startOrSendMessage = async () => {
             if (isLoading.value || userInput.value.trim() === '') return;

             if (!chatStarted.value) {
                chatStarted.value = true;
                // Need nextTick to ensure chat view elements are rendered before sending
                await nextTick(); 
            }
            sendMessage();
        };

        const sendMessage = async () => {
            // This function now assumes chatStarted is true
            if (isLoading.value || userInput.value.trim() === '') return;

            const messageContent = userInput.value.trim();
            isLoading.value = true;
            userInput.value = ''; // Clear input

            // Add user message to history
            const userMessage = { id: Date.now(), role: 'user', content: messageContent };
            history.value.push(userMessage);
            scrollToBottom(); 

            // 如果启用了网络搜索，先执行搜索
            if (useWebSearch.value) {
                await performWebSearch();
            }

            try {
                // Prepare messages for API (include system messages if any were ingested via API)
                // Note: The current API server resets on each call, so history building here is
                // mostly for the *next* call if the server state were preserved.
                const messagesForApi = history.value.map(msg => ({ role: msg.role, content: msg.content }));
                
                console.log("Sending messages to API:", JSON.stringify(messagesForApi));
                
                // 添加重试逻辑
                let retries = 3;
                let response = null;
                
                // 决定使用哪个API端点
                const apiEndpoint = useCoT.value ? 
                    `${apiUrl.value}/v1/chat/completions/cot` : 
                    `${apiUrl.value}/v1/chat/completions`;
                
                while (retries > 0) {
                    try {
                        response = await fetch(apiEndpoint, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({
                                model: 'openkimi-model', 
                                messages: messagesForApi,
                            }),
                        });
                        
                        // 如果响应成功，跳出循环
                        if (response.ok) {
                            break;
                        }
                        
                        // 如果是503错误（服务器初始化问题），等待一会再重试
                        if (response.status === 503) {
                            console.log(`服务器报告503错误，剩余重试次数: ${retries-1}`);
                            await new Promise(resolve => setTimeout(resolve, 1000)); // 等待1秒
                            retries--;
                        } else {
                            // 其他错误直接跳出循环
                            break;
                        }
                    } catch (fetchError) {
                        console.error("Fetch error:", fetchError);
                        retries--;
                        if (retries > 0) {
                            console.log(`网络错误，剩余重试次数: ${retries}`);
                            await new Promise(resolve => setTimeout(resolve, 1000)); // 等待1秒
                        }
                    }
                }
                
                if (!response || !response.ok) {
                    const errorData = await response?.json().catch(() => ({ detail: '无法解析错误响应' }));
                    throw new Error(`API Error (${response?.status}): ${errorData.detail || response?.statusText || "无法连接到服务器"}`);
                }

                const data = await response.json();
                console.log("Received data from API:", data);
                
                if (data.choices && data.choices.length > 0 && data.choices[0].message) {
                    const assistantMessage = { 
                        id: Date.now() + 1, 
                        role: 'assistant', 
                        content: data.choices[0].message.content.trim() 
                    };
                    history.value.push(assistantMessage);
                } else {
                    throw new Error('API 响应格式无效');
                }

            } catch (error) {
                console.error('Send Message Error:', error);
                history.value.push({
                    id: Date.now() + 1,
                    role: 'assistant',
                    content: `发生错误: ${error.message}`
                });
            } finally {
                isLoading.value = false;
                scrollToBottom(); 
            }
        };

        const resetChat = () => {
            history.value = [];
            userInput.value = '';
            isLoading.value = false;
            uploadedFiles.value = []; // 清空已上传的文件列表
            chatStarted.value = false; // Go back to initial view
            // API server reset happens automatically on next request in current implementation
            fetchSuggestions(); // Fetch new suggestions when resetting to initial view
        };

        // --- UI Helpers ---
        const scrollToBottom = () => {
            nextTick(() => {
                const container = chatHistory.value;
                if (container) {
                    container.scrollTop = container.scrollHeight;
                }
            });
        };

        const renderMarkdown = (content) => {
             // Ensure content is a string
            const textContent = String(content || '');
            if (typeof marked === 'undefined') {
                console.warn('Marked library not loaded!');
                return textContent.replace(/\n/g, '<br>');
            }
            try {
                 // Basic sanitization (consider DOMPurify for production)
                const dirtyHtml = marked.parse(textContent);
                 // Replace <a href...> with <a target="_blank"...
                return dirtyHtml.replace(/<a\s+(?:[^>]*?\s+)?href="([^"*]*)"/g, '<a target="_blank" rel="noopener noreferrer" href="$1"');
            } catch (e) {
                console.error("Markdown rendering error:", e);
                return textContent.replace(/\n/g, '<br>'); // Fallback
            }
        };

        const useSuggestion = (suggestion) => {
            userInput.value = suggestion;
            // Automatically start the chat and send the message
            startOrSendMessage();
        };

        // --- Lifecycle Hooks ---
        onMounted(() => {
            checkApiStatus(); // Check API status on load
            fetchSuggestions(); // Fetch suggestions on load
        });

        return {
            history,
            userInput,
            isLoading,
            apiUrl,
            apiStatus,
            chatHistory,
            chatStarted, // Expose new state
            suggestions, // Expose suggestions
            suggestionsLoading, // Expose loading state
            fileInput, // 文件输入引用
            uploadedFiles, // 已上传的文件
            isUploading, // 文件上传状态
            handleFileUpload, // 文件上传处理
            triggerFileUpload, // 触发文件上传对话框
            sendMessage, // Keep original for internal use
            startOrSendMessage, // Use this for UI buttons/enter key
            resetChat,
            checkApiStatus,
            renderMarkdown,
            useSuggestion, // Expose suggestion handler
            useCoT,
            useWebSearch,
            isSearching,
            searchResults,
            sidebarOpen,
            activeTab,
            toggleCoT,
            toggleWebSearch,
            performWebSearch,
            toggleSidebar,
            setActiveTab,
            searchOnlyWeb
        };
    }
};

createApp(App).mount('#app'); 