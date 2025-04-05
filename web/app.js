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
                localStorage.setItem('openKimiApiUrl', apiUrl.value);
            } catch (error) {
                console.error('API Status Check Error:', error);
                apiStatus.value = `连接失败`; // Simplified error message
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

            try {
                // Prepare messages for API (include system messages if any were ingested via API)
                // Note: The current API server resets on each call, so history building here is
                // mostly for the *next* call if the server state were preserved.
                const messagesForApi = history.value.map(msg => ({ role: msg.role, content: msg.content }));
                
                console.log("Sending messages to API:", JSON.stringify(messagesForApi));

                const response = await fetch(`${apiUrl.value}/v1/chat/completions`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        model: 'openkimi-model', 
                        messages: messagesForApi,
                    }),
                });

                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({ detail: '无法解析错误响应' }));
                    throw new Error(`API Error (${response.status}): ${errorData.detail || response.statusText}`);
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
            sendMessage, // Keep original for internal use
            startOrSendMessage, // Use this for UI buttons/enter key
            resetChat,
            checkApiStatus,
            renderMarkdown,
            useSuggestion // Expose suggestion handler
        };
    }
};

createApp(App).mount('#app'); 