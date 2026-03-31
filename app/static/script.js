document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatMessages = document.getElementById('chat-messages');
    const sendButton = document.getElementById('send-button');
    const typingIndicator = document.getElementById('typing-indicator');
    const authCheck = document.getElementById('auth-check');
    const chatInterface = document.getElementById('chat-interface');
    const inputArea = document.getElementById('input-area');
    const userGreeting = document.getElementById('user-greeting');
    const welcomeMessage = document.getElementById('welcome-message');
    
    // Generate a unique session ID for this page load
    const sessionId = 'sess_' + Math.random().toString(36).substring(2, 9);

    // Check authentication on page load
    checkAuthentication();

    // Auto-scroll to bottom
    const scrollToBottom = () => {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    };

    // Check authentication status
    async function checkAuthentication() {
        const token = localStorage.getItem('auth_token');
        
        if (!token) {
            // No token, redirect to login
            window.location.href = '/';
            return;
        }

        try {
            // Verify token with server
            const response = await fetch('/auth/verify', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                const userData = await response.json();
                // Authentication successful, show chat interface
                showChatInterface(userData.user);
            } else {
                // Token invalid, redirect to login
                localStorage.removeItem('auth_token');
                window.location.href = '/';
            }
        } catch (error) {
            console.error('Auth check failed:', error);
            localStorage.removeItem('auth_token');
            window.location.href = '/';
        }
    }

    // Show chat interface after successful authentication
    function showChatInterface(user) {
        authCheck.style.display = 'none';
        chatInterface.style.display = 'block';
        inputArea.style.display = 'block';
        
        // Update greeting
        userGreeting.textContent = `Welcome, ${user.first_name}`;
        welcomeMessage.textContent = `Hello ${user.first_name}! I'm your therapy assistant. How are you feeling today?`;
    }

    // Enable/disable send button
    userInput.addEventListener('input', () => {
        if (userInput.value.trim().length > 0) {
            sendButton.removeAttribute('disabled');
        } else {
            sendButton.setAttribute('disabled', 'true');
        }
    });

    // Create message element
    const createMessageElement = (content, role) => {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', `${role}-message`);

        const avatarDiv = document.createElement('div');
        avatarDiv.classList.add('avatar', `${role}-avatar`);
        avatarDiv.textContent = role === 'user' ? 'U' : 'R';

        const contentDiv = document.createElement('div');
        contentDiv.classList.add('message-content');
        
        // Very basic markdown formatting for bold and code blocks
        let formattedContent = content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
            .replace(/`([^`]+)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>');
            
        contentDiv.innerHTML = formattedContent;

        messageDiv.appendChild(avatarDiv);
        messageDiv.appendChild(contentDiv);

        return messageDiv;
    };

    // Handle form submission
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const query = userInput.value.trim();
        if (!query) return;

        // Add user message
        const userMessage = createMessageElement(query, 'user');
        chatMessages.appendChild(userMessage);
        
        // Clear input and disable button
        userInput.value = '';
        sendButton.setAttribute('disabled', 'true');
        scrollToBottom();

        // Show typing indicator
        typingIndicator.style.display = 'flex';
        chatMessages.appendChild(typingIndicator);
        scrollToBottom();

        try {
            const token = localStorage.getItem('auth_token');
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ query: query, session_id: sessionId })
            });

            const contentType = response.headers.get('content-type') || '';
            const data = contentType.includes('application/json')
                ? await response.json()
                : { detail: await response.text() };
            
            // Hide typing indicator
            typingIndicator.style.display = 'none';

            if (response.ok) {
                const assistantMessage = createMessageElement(data.answer, 'assistant');
                chatMessages.appendChild(assistantMessage);
            } else {
                if (response.status === 401 || response.status === 403) {
                    localStorage.removeItem('auth_token');
                    window.location.href = '/';
                    return;
                }
                throw new Error(data.detail || 'Failed to get response');
            }
        } catch (error) {
            typingIndicator.style.display = 'none';
            const errorMessage = createMessageElement(`Error: ${error.message}`, 'assistant');
            errorMessage.querySelector('.message-content').style.color = '#ff7b72';
            chatMessages.appendChild(errorMessage);
        }
        
        scrollToBottom();
        // Return focus to input
        userInput.focus();
    });
});
