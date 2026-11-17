async function logout() {
  await fetch('/admin/logout', { method: 'POST', credentials: 'same-origin' });
  window.location.href = 'login.html';
}

async function refreshAuthUI() {
  const container = document.querySelector('.auth-actions');
  if (!container) return;
  try {
    const response = await fetch('/admin/me', { credentials: 'same-origin' });
    if (!response.ok) return;
    const data = await response.json();
    const user = data.user;
    let html = '<span class="user-name">' + user.username + '</span>';
    if (user.role === 'admin') {
      html += '<a class="btn btn-secondary" href="../admin/users.html">Admin</a>';
    }
    html += '<button class="btn btn-secondary" type="button" onclick="logout()">Đăng xuất</button>';
    container.innerHTML = html;
  } catch (error) {
    // Keep the default login button when the user is not authenticated.
  }
}

document.addEventListener('DOMContentLoaded', refreshAuthUI);
