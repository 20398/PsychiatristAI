document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatMessages = document.getElementById('chat-messages');
    const sendButton = document.getElementById('send-button');
    const typingIndicator = document.getElementById('typing-indicator');
    
    // Generate a unique session ID for this page load
    const sessionId = 'sess_' + Math.random().toString(36).substring(2, 9);

    // Auto-scroll to bottom
    const scrollToBottom = () => {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    };

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
            .replace(/```([\s\S]*?)```/g, '<pre style="background: rgba(0,0,0,0.3); padding: 12px; border-radius: 8px; margin-top: 8px; overflow-x: auto;"><code>$1</code></pre>')
            .replace(/`([^`]+)`/g, '<code style="background: rgba(0,0,0,0.3); padding: 2px 4px; border-radius: 4px;">$1</code>')
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
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ query: query, session_id: sessionId })
            });

            const data = await response.json();
            
            // Hide typing indicator
            typingIndicator.style.display = 'none';

            if (response.ok) {
                // Add assistant message
                const assistantMessage = createMessageElement(data.answer, 'assistant');
                chatMessages.appendChild(assistantMessage);
            } else {
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
