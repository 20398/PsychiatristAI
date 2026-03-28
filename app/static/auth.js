// Authentication JavaScript
let currentToken = localStorage.getItem('auth_token');
let currentUser = null;

// Check if user is logged in on page load
document.addEventListener('DOMContentLoaded', function() {
    if (currentToken) {
        // Verify token and redirect to chat
        fetch('/auth/verify', {
            headers: {
                'Authorization': `Bearer ${currentToken}`
            }
        })
        .then(response => {
            if (response.ok) {
                window.location.href = '/chat';
            } else {
                localStorage.removeItem('auth_token');
                currentToken = null;
            }
        })
        .catch(() => {
            localStorage.removeItem('auth_token');
            currentToken = null;
        });
    }
});

function showLogin() {
    document.querySelector('.auth-buttons').style.display = 'none';
    document.querySelector('.google-auth').style.display = 'none';

    const loginForm = document.createElement('div');
    loginForm.className = 'auth-form active';
    loginForm.innerHTML = `
        <h2>Login</h2>
        <form onsubmit="handleLogin(event)">
            <div class="form-group">
                <label for="email">Email</label>
                <input type="email" id="email" required>
            </div>
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" required>
            </div>
            <button type="submit" class="btn-submit">Login</button>
        </form>
        <div class="back-link" onclick="showLanding()">← Back</div>
    `;

    document.querySelector('.auth-card').appendChild(loginForm);
}

function showRegister() {
    document.querySelector('.auth-buttons').style.display = 'none';
    document.querySelector('.google-auth').style.display = 'none';

    // First load genders
    fetch('/auth/genders')
        .then(response => response.json())
        .then(genders => {
            const registerForm = document.createElement('div');
            registerForm.className = 'auth-form active';
            registerForm.innerHTML = `
                <h2>Create Account</h2>
                <form onsubmit="handleRegister(event)">
                    <div class="form-group">
                        <label for="first_name">First Name</label>
                        <input type="text" id="first_name" required>
                    </div>
                    <div class="form-group">
                        <label for="last_name">Last Name</label>
                        <input type="text" id="last_name" required>
                    </div>
                    <div class="form-group">
                        <label for="phone">Phone Number</label>
                        <input type="tel" id="phone">
                    </div>
                    <div class="form-group">
                        <label for="email">Email</label>
                        <input type="email" id="email" required>
                    </div>
                    <div class="form-group">
                        <label for="gender">Gender</label>
                        <select id="gender" required>
                            <option value="">Select Gender</option>
                            ${genders.map(g => `<option value="${g.id}">${g.name}</option>`).join('')}
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="password">Password</label>
                        <input type="password" id="password" required minlength="8">
                    </div>
                    <button type="submit" class="btn-submit">Create Account</button>
                </form>
                <div class="back-link" onclick="showLanding()">← Back</div>
            `;

            document.querySelector('.auth-card').appendChild(registerForm);
        });
}

function showLanding() {
    // Remove forms
    document.querySelectorAll('.auth-form').forEach(form => form.remove());

    // Show buttons
    document.querySelector('.auth-buttons').style.display = 'flex';
    document.querySelector('.google-auth').style.display = 'block';
}

function handleLogin(event) {
    event.preventDefault();

    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    fetch('/auth/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email, password })
    })
    .then(response => {
        if (response.ok) {
            return response.json();
        } else {
            // Handle both JSON and non-JSON error responses
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return response.json().then(err => { throw new Error(err.detail || 'Login failed'); });
            } else {
                return response.text().then(text => { throw new Error('Login failed: ' + text.substring(0, 100)); });
            }
        }
    })
    .then(data => {
        localStorage.setItem('auth_token', data.access_token);
        currentToken = data.access_token;
        window.location.href = '/chat';
    })
    .catch(error => {
        alert('Login failed. Please check your credentials.');
        console.error('Login error:', error);
    });
}

function handleRegister(event) {
    event.preventDefault();

    const userData = {
        first_name: document.getElementById('first_name').value,
        last_name: document.getElementById('last_name').value,
        phone: document.getElementById('phone').value,
        email: document.getElementById('email').value,
        gender_id: parseInt(document.getElementById('gender').value),
        password: document.getElementById('password').value
    };

    fetch('/auth/register', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(userData)
    })
    .then(response => {
        if (response.ok) {
            return response.json();
        } else {
            // Handle both JSON and non-JSON error responses
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return response.json().then(err => { throw new Error(err.detail || 'Registration failed'); });
            } else {
                return response.text().then(text => { throw new Error('Registration failed: ' + text.substring(0, 100)); });
            }
        }
    })
    .then(data => {
        localStorage.setItem('auth_token', data.access_token);
        currentToken = data.access_token;
        window.location.href = '/chat';
    })
    .catch(error => {
        alert(error.message);
        console.error('Registration error:', error);
    });
}

function googleLogin() {
    // For now, show a message. In production, implement Google OAuth
    alert('Google login will be implemented soon. Please use email registration for now.');
}

function logout() {
    localStorage.removeItem('auth_token');
    currentToken = null;
    window.location.href = '/';
}