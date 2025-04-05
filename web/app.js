const { createApp, ref, onMounted, nextTick } = Vue;

const App = {
    setup() {
        const history = ref([]); // Stores chat messages {id, role, content}
        const userInput = ref('');
        const isLoading = ref(false);
        const apiUrl = ref(localStorage.getItem('openKimiApiUrl') || 'http://127.0.0.1:8000'); // Default API URL
        const apiStatus = ref('未知');
        const chatHistory = ref(null); // Ref for the chat history div

        // --- API Interaction ---
        const checkApiStatus = async () => {
            apiStatus.value = '检查中...';
            try {
                const response = await fetch(`${apiUrl.value}/health`);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const data = await response.json();
                if (data.status === 'ok' && data.engine_initialized) {
                    apiStatus.value = `正常 (${data.model_name})`;
                } else {
                    apiStatus.value = `错误: ${data.detail || '引擎未初始化'}`;
                }
                // Save API URL on successful check
                localStorage.setItem('openKimiApiUrl', apiUrl.value);
            } catch (error) {
                console.error('API Status Check Error:', error);
                apiStatus.value = `连接失败: ${error.message}`;
            }
        };

        const sendMessage = async () => {
            if (isLoading.value || userInput.value.trim() === '') return;

            const messageContent = userInput.value.trim();
            isLoading.value = true;
            userInput.value = ''; // Clear input

            // Add user message to history
            const userMessage = { id: Date.now(), role: 'user', content: messageContent };
            history.value.push(userMessage);
            scrollToBottom(); // Scroll after adding user message

            try {
                // Prepare OpenAI-like message format
                const messages = history.value.map(msg => ({ role: msg.role, content: msg.content }));
                // Make sure the last message is the current user input
                if (messages.length === 0 || messages[messages.length - 1].role !== 'user') {
                    messages.push({ role: 'user', content: messageContent });
                }
                
                console.log("Sending messages:", JSON.stringify(messages));

                const response = await fetch(`${apiUrl.value}/v1/chat/completions`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        model: 'openkimi-model', // Model name is currently ignored by the server
                        messages: messages,
                        // Add other parameters like temperature if needed
                    }),
                });

                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({ detail: '无法解析错误响应' }));
                    throw new Error(`API Error (${response.status}): ${errorData.detail || response.statusText}`);
                }

                const data = await response.json();
                console.log("Received data:", data);
                
                if (data.choices && data.choices.length > 0 && data.choices[0].message) {
                    const assistantMessage = { 
                        id: Date.now() + 1, // Ensure unique ID
                        role: 'assistant', 
                        content: data.choices[0].message.content.trim() 
                    };
                    history.value.push(assistantMessage);
                } else {
                    throw new Error('API 响应格式无效');
                }

            } catch (error) {
                console.error('Send Message Error:', error);
                // Add error message to chat
                history.value.push({
                    id: Date.now() + 1,
                    role: 'assistant',
                    content: `发生错误: ${error.message}`
                });
            } finally {
                isLoading.value = false;
                scrollToBottom(); // Scroll after receiving response
            }
        };

        const resetChat = () => {
            history.value = [];
            userInput.value = '';
            isLoading.value = false;
            // Optionally ping the server's reset if it existed
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
            if (typeof marked === 'undefined') {
                console.error('Marked library not loaded!');
                // Simple rendering as fallback
                return content.replace(/\n/g, '<br>');
            }
            // Basic sanitization (consider a more robust library like DOMPurify for production)
            const dirtyHtml = marked.parse(content);
            // VERY basic link target setting
            return dirtyHtml.replace(/<a href/g, '<a target="_blank" rel="noopener noreferrer" href');
        };

        // --- Lifecycle Hooks ---
        onMounted(() => {
            checkApiStatus(); // Check API status on load
        });

        return {
            history,
            userInput,
            isLoading,
            apiUrl,
            apiStatus,
            chatHistory,
            sendMessage,
            resetChat,
            checkApiStatus,
            renderMarkdown
        };
    }
};

createApp(App).mount('#app'); 