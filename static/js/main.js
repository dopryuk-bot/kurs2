'use strict';

// ── Sidebar toggle (mobile) ───────────────────────────────────────────────
const sidebar = document.getElementById('sidebar');
const overlay = document.getElementById('sidebarOverlay');
const openBtn = document.getElementById('sidebarOpen');
const closeBtn = document.getElementById('sidebarClose');

function openSidebar() {
  sidebar?.classList.add('open');
  overlay?.classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closeSidebar() {
  sidebar?.classList.remove('open');
  overlay?.classList.remove('open');
  document.body.style.overflow = '';
}

openBtn?.addEventListener('click', openSidebar);
closeBtn?.addEventListener('click', closeSidebar);
overlay?.addEventListener('click', closeSidebar);

// ── Auto-dismiss alerts ───────────────────────────────────────────────────
document.querySelectorAll('.alert:not(.alert-danger)').forEach(el => {
  setTimeout(() => {
    const bsAlert = bootstrap.Alert.getOrCreateInstance(el);
    bsAlert?.close();
  }, 5000);
});
