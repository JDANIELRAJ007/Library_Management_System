// ── EduLib Main JS ──────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {

  // Init AOS
  if (typeof AOS !== 'undefined') AOS.init({ duration: 700, once: true, offset: 60 });

  // ── Theme Toggle ──────────────────────────────────────────
  const html = document.documentElement;
  const themeBtn = document.getElementById('theme-toggle');
  const themeIcon = document.getElementById('theme-icon');
  const saved = localStorage.getItem('edulib-theme') || 'dark';
  html.setAttribute('data-theme', saved);
  updateThemeIcon(saved);

  if (themeBtn) {
    themeBtn.addEventListener('click', () => {
      const current = html.getAttribute('data-theme');
      const next = current === 'dark' ? 'light' : 'dark';
      html.setAttribute('data-theme', next);
      localStorage.setItem('edulib-theme', next);
      updateThemeIcon(next);
    });
  }
  function updateThemeIcon(theme) {
    const btn = document.getElementById('theme-toggle');
    if (!btn) return;
    const iconName = theme === 'dark' ? 'sun' : 'moon';
    btn.innerHTML = `<i data-lucide="${iconName}"></i>`;
    if (typeof lucide !== 'undefined') lucide.createIcons({ root: btn });
  }

  // ── Sidebar Toggle (mobile) ───────────────────────────────
  const sidebar = document.getElementById('sidebar');
  const sidebarToggle = document.getElementById('sidebar-toggle');
  const sidebarOverlay = document.getElementById('sidebar-overlay');
  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener('click', () => {
      sidebar.classList.toggle('open');
      sidebarOverlay.classList.toggle('open');
    });
  }
  if (sidebarOverlay) {
    sidebarOverlay.addEventListener('click', () => {
      sidebar.classList.remove('open');
      sidebarOverlay.classList.remove('open');
    });
  }

  // ── Auto-dismiss flash messages ───────────────────────────
  document.querySelectorAll('#flash-container .alert').forEach(el => {
    setTimeout(() => el.remove(), 5000);
  });

  // ── Chatbot ───────────────────────────────────────────────
  const widget  = document.getElementById('chatbot-widget');
  const toggle  = document.getElementById('chatbot-toggle');
  const msgs    = document.getElementById('chat-messages');
  const input   = document.getElementById('chat-input');
  const sendBtn = document.getElementById('chat-send');

  if (toggle) {
    toggle.addEventListener('click', () => {
      widget.classList.toggle('collapsed');
      widget.classList.toggle('expanded');
    });
  }

  function appendMsg(text, isUser) {
    const div = document.createElement('div');
    div.className = 'message ' + (isUser ? 'user-msg' : 'bot-msg');
    div.textContent = text;
    msgs.appendChild(div);
    msgs.scrollTop = msgs.scrollHeight;
    return div;
  }

  async function sendChat() {
    if (!input) return;
    const text = input.value.trim();
    if (!text) return;
    appendMsg(text, true);
    input.value = '';

    const loader = appendMsg('…', false);
    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text })
      });
      const data = await res.json();
      loader.textContent = data.response || data.error || 'Something went wrong.';
    } catch {
      loader.textContent = 'Network error. Please try again.';
    }
    msgs.scrollTop = msgs.scrollHeight;
  }

  if (sendBtn) sendBtn.addEventListener('click', sendChat);
  if (input) input.addEventListener('keypress', e => { if (e.key === 'Enter') sendChat(); });

  // ── Notification Dot ──────────────────────────────────────
  const notifDot = document.getElementById('notif-dot');
  if (notifDot) {
    fetch('/api/notifications/count')
      .then(r => r.json())
      .then(d => { if (d.count > 0) notifDot.style.display = 'block'; })
      .catch(() => {});
  }

  // ── Confirm Dialogs ───────────────────────────────────────
  document.querySelectorAll('[data-confirm]').forEach(btn => {
    btn.addEventListener('click', e => {
      if (!confirm(btn.dataset.confirm)) e.preventDefault();
    });
  });

  // ── Lucide Icons ──────────────────────────────────────────
  if (typeof lucide !== 'undefined') {
    lucide.createIcons();
  }
});
