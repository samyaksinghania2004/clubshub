(function () {
  const html = document.documentElement;
  const sidebar = document.querySelector('[data-app-sidebar]');
  const sidebarToggle = document.querySelector('[data-sidebar-toggle]');
  const appShell = document.querySelector('.app-shell');
  const desktopSidebarQuery = window.matchMedia('(min-width: 1025px)');
  const themeToggle = document.querySelector('[data-theme-toggle]');
  const enableAlertsButton = document.querySelector('[data-enable-browser-notifications]');
  const toastRoot = document.getElementById('toast-root');
  const themeKey = 'clubshub-theme';
  const seenNotificationsKey = 'clubshub-seen-notification-ids';

  const showToast = (title, body) => {
    if (!toastRoot) return;
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.innerHTML = `<h4>${title}</h4><p>${body || ''}</p>`;
    toastRoot.appendChild(toast);
    window.setTimeout(() => toast.remove(), 5500);
  };

  const loadTheme = () => {
    const saved = localStorage.getItem(themeKey);
    if (saved) {
      html.setAttribute('data-theme', saved);
    }
  };

  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener('click', () => {
      if (desktopSidebarQuery.matches) {
        appShell?.classList.toggle('is-sidebar-collapsed');
      } else {
        sidebar.classList.toggle('is-open');
      }
    });
  }

  loadTheme();
  if (themeToggle) {
    themeToggle.addEventListener('click', () => {
      const next = html.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
      html.setAttribute('data-theme', next);
      localStorage.setItem(themeKey, next);
    });
  }

  const canUseBrowserNotifications = () => 'Notification' in window && window.isSecureContext;

  if (enableAlertsButton) {
    enableAlertsButton.addEventListener('click', async () => {
      if (!('Notification' in window)) {
        showToast('Notifications unavailable', 'Your browser does not support desktop notifications.');
        return;
      }
      if (!window.isSecureContext) {
        showToast('HTTPS required', 'Desktop browser notifications require HTTPS or localhost.');
        return;
      }
      const permission = await Notification.requestPermission();
      if (permission === 'granted') {
        showToast('Desktop alerts enabled', 'New ClubsHub updates will appear as browser notifications.');
      } else {
        showToast('Permission denied', 'Desktop alerts were not enabled.');
      }
    });
  }

  const getSeenIds = () => {
    try {
      return new Set(JSON.parse(localStorage.getItem(seenNotificationsKey) || '[]'));
    } catch {
      return new Set();
    }
  };

  const saveSeenIds = (ids) => {
    localStorage.setItem(seenNotificationsKey, JSON.stringify(Array.from(ids).slice(-60)));
  };

  const pollNotifications = async () => {
    const url = window.clubshubNotificationFeedUrl;
    if (!url) return;
    try {
      const response = await fetch(url, { credentials: 'same-origin' });
      if (!response.ok) return;
      const payload = await response.json();
      const badge = document.querySelector('.badge-pill');
      if (badge) {
        badge.textContent = payload.unread_count;
      }
      const seen = getSeenIds();
      payload.items.forEach((item) => {
        if (seen.has(item.id)) return;
        seen.add(item.id);
        if (canUseBrowserNotifications() && Notification.permission === 'granted') {
          const notification = new Notification(item.title, {
            body: item.body || 'Open ClubsHub to view this update.',
          });
          notification.onclick = () => {
            window.location.href = item.url;
          };
        } else {
          showToast(item.title, item.body || 'Open ClubsHub to view this update.');
        }
      });
      saveSeenIds(seen);
    } catch (error) {
      console.debug('Notification polling failed', error);
    }
  };

  if (window.clubshubNotificationFeedUrl) {
    pollNotifications();
    window.setInterval(pollNotifications, 60000);
  }

  const confirmForms = document.querySelectorAll('form[data-confirm]');
  confirmForms.forEach((form) => {
    form.addEventListener('submit', (event) => {
      const message = form.getAttribute('data-confirm');
      if (message && !window.confirm(message)) {
        event.preventDefault();
      }
    });
  });

  const closeActionMenus = () => {
    document.querySelectorAll('details.action-menu[open]').forEach((menu) => {
      menu.removeAttribute('open');
    });
  };

  document.addEventListener(
    'click',
    (event) => {
      const openMenus = document.querySelectorAll('details.action-menu[open]');
      if (!openMenus.length) return;
      const clickedInside = Array.from(openMenus).some((menu) => menu.contains(event.target));
      if (clickedInside) return;
      closeActionMenus();
      event.preventDefault();
      event.stopPropagation();
    },
    true,
  );

  const userSearchInputs = document.querySelectorAll('[data-user-search]');
  userSearchInputs.forEach((input) => {
    const wrapper = document.createElement('div');
    wrapper.className = 'autocomplete';
    input.parentNode.insertBefore(wrapper, input);
    wrapper.appendChild(input);

    const list = document.createElement('div');
    list.className = 'autocomplete-list is-hidden';
    wrapper.appendChild(list);

    let debounceTimer;
    let abortController;

    const clearList = () => {
      list.innerHTML = '';
      list.classList.add('is-hidden');
    };

    const renderItems = (items) => {
      list.innerHTML = '';
      if (!items.length) {
        list.classList.add('is-hidden');
        return;
      }
      items.forEach((item) => {
        const option = document.createElement('button');
        option.type = 'button';
        option.className = 'autocomplete-item';
        option.textContent = item.label || item.email || item.username;
        option.addEventListener('click', () => {
          input.value = item.username || '';
          clearList();
        });
        list.appendChild(option);
      });
      list.classList.remove('is-hidden');
    };

    const search = (value) => {
      const url = window.clubshubUserSearchUrl;
      if (!url) return;
      if (abortController) {
        abortController.abort();
      }
      abortController = new AbortController();
      fetch(`${url}?q=${encodeURIComponent(value)}`, { signal: abortController.signal })
        .then((response) => (response.ok ? response.json() : { items: [] }))
        .then((payload) => renderItems(payload.items || []))
        .catch(() => {
          clearList();
        });
    };

    input.setAttribute('autocomplete', 'off');
    input.addEventListener('input', (event) => {
      const value = event.target.value.trim();
      window.clearTimeout(debounceTimer);
      if (value.length < 2) {
        clearList();
        return;
      }
      debounceTimer = window.setTimeout(() => search(value), 220);
    });

    input.addEventListener('blur', () => {
      window.setTimeout(() => clearList(), 120);
    });
  });

  const openModal = (modal, focusId) => {
    if (!modal) return;
    modal.classList.remove('is-hidden');
    document.body.classList.add('modal-open');
    if (focusId) {
      const focusTarget = modal.querySelector(`#${focusId}`);
      if (focusTarget) {
        window.setTimeout(() => focusTarget.focus(), 0);
      }
    }
  };

  const closeModal = (modal) => {
    if (!modal) return;
    modal.classList.add('is-hidden');
    if (document.querySelectorAll('.modal:not(.is-hidden)').length === 0) {
      document.body.classList.remove('modal-open');
    }
  };

  const modalTriggers = document.querySelectorAll('[data-modal-target]');
  modalTriggers.forEach((trigger) => {
    trigger.addEventListener('click', () => {
      const target = trigger.getAttribute('data-modal-target');
      const focusId = trigger.getAttribute('data-modal-focus');
      if (!target) return;
      const modal = document.getElementById(target);
      openModal(modal, focusId);
    });
  });

  const modalCloseTargets = document.querySelectorAll('[data-modal-close]');
  modalCloseTargets.forEach((closer) => {
    closer.addEventListener('click', (event) => {
      const modal = event.target.closest('.modal');
      closeModal(modal);
    });
  });

  document.addEventListener('keydown', (event) => {
    if (event.key !== 'Escape') return;
    const openModalEl = document.querySelector('.modal:not(.is-hidden)');
    if (openModalEl) {
      closeModal(openModalEl);
    }
  });

  const focused = document.querySelector('.chat-message.is-focused');
  if (focused) {
    focused.scrollIntoView({ block: 'center', behavior: 'smooth' });
  }
})();
