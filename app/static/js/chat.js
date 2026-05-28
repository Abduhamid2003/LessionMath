const ChatApp = {
  rooms: [],
  contacts: [],
  currentRoomId: null,
  ws: null,
  heartbeat: null,
  searchTimer: null,

  async init() {
    if (!Auth.token) {
      location.href = '/login';
      return;
    }
    document.getElementById('chatForm')?.addEventListener('submit', e => {
      e.preventDefault();
      this.sendMessage();
    });
    const searchInput = document.getElementById('contactSearch');
    searchInput?.addEventListener('input', () => {
      clearTimeout(this.searchTimer);
      this.searchTimer = setTimeout(() => this.loadContacts(searchInput.value.trim()), 250);
    });
    await this.loadContacts('');
    await this.loadRooms();
    this.heartbeat = setInterval(() => API.post('/api/chat/presence', {}), 25000);
  },

  roleLabel(role) {
    const map = { student: I18n.t('chat.roleStudent'), teacher: I18n.t('chat.roleTeacher'), admin: I18n.t('chat.roleAdmin') };
    return map[role] || role;
  },

  async loadContacts(q) {
    const url = q ? `/api/chat/contacts?q=${encodeURIComponent(q)}` : '/api/chat/contacts';
    this.contacts = await API.get(url);
    const el = document.getElementById('contactsList');
    if (!el) return;
    if (!this.contacts.length) {
      el.innerHTML = `<p class="text-muted small mb-0">${I18n.t('chat.noContacts')}</p>`;
      return;
    }
    el.innerHTML = this.contacts
      .map(
        c => `<button type="button" class="chat-contact-item" data-user="${c.id}">
          <span class="online-dot ${c.online ? 'on' : 'off'}"></span>
          <strong>${this.escape(c.full_name || c.username)}</strong>
          <br><small class="text-muted">@${this.escape(c.username)} · ${this.escape(this.roleLabel(c.role))}</small>
        </button>`
      )
      .join('');
    el.querySelectorAll('.chat-contact-item').forEach(btn => {
      btn.addEventListener('click', () => this.startDirect(parseInt(btn.dataset.user, 10)));
    });
  },

  async startDirect(userId) {
    const room = await API.post(`/api/chat/direct/with/${userId}`, {});
    await this.loadRooms();
    this.selectRoom(room.id);
  },

  async loadRooms() {
    this.rooms = await API.get('/api/chat/rooms');
    const el = document.getElementById('roomsList');
    el.innerHTML = this.rooms.length
      ? this.rooms
          .map(
            r => `<div class="chat-room-item ${r.id === this.currentRoomId ? 'active' : ''}" data-room="${r.id}">
            <strong>${this.escape(r.title || (r.room_type === 'class' ? I18n.t('chat.classRoom') : I18n.t('chat.directRoom')))}</strong>
            <br><small class="text-muted">${this.escape(r.last_message || '')}</small>
          </div>`
          )
          .join('')
      : `<p class="text-muted small">${I18n.t('chat.noRooms')}</p>`;
    el.querySelectorAll('.chat-room-item').forEach(item => {
      item.addEventListener('click', () => this.selectRoom(parseInt(item.dataset.room, 10)));
    });
  },

  async selectRoom(roomId) {
    this.currentRoomId = roomId;
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    const room = this.rooms.find(r => r.id === roomId);
    document.getElementById('chatRoomTitle').textContent = room?.title || 'Chat';
    document.getElementById('chatInput').disabled = false;
    document.getElementById('chatSendBtn').disabled = false;
    await this.loadMessages();
    await this.loadOnline();
    this.connectWs(roomId);
    await this.loadRooms();
  },

  async loadMessages() {
    const msgs = await API.get(`/api/chat/rooms/${this.currentRoomId}/messages`);
    const box = document.getElementById('messagesBox');
    box.innerHTML = msgs.map(m => this.bubbleHtml(m)).join('');
    box.scrollTop = box.scrollHeight;
  },

  bubbleHtml(m) {
    const mine = m.sender_id === Auth.user.id;
    return `<div class="chat-bubble ${mine ? 'mine' : 'other'}">
      <small class="opacity-75">${this.escape(m.sender_name)}</small><br>
      ${this.escape(m.content)}
    </div>`;
  },

  async loadOnline() {
    const users = await API.get(`/api/chat/rooms/${this.currentRoomId}/online`);
    document.getElementById('onlineUsers').innerHTML = users
      .map(
        u =>
          `<span class="me-2"><span class="online-dot ${u.online ? 'on' : 'off'}"></span>${this.escape(u.username)}</span>`
      )
      .join('');
  },

  connectWs(roomId) {
    const proto = location.protocol === 'https:' ? 'wss' : 'ws';
    this.ws = new WebSocket(`${proto}://${location.host}/api/chat/ws/${roomId}?token=${Auth.token}`);
    this.ws.onmessage = ev => {
      const data = JSON.parse(ev.data);
      if (data.type === 'message') {
        const box = document.getElementById('messagesBox');
        box.insertAdjacentHTML('beforeend', this.bubbleHtml(data));
        box.scrollTop = box.scrollHeight;
      }
      if (data.type === 'presence') this.loadOnline();
    };
    this.ws.onopen = () => {
      setInterval(() => this.ws?.readyState === 1 && this.ws.send(JSON.stringify({ type: 'ping' })), 20000);
    };
  },

  async sendMessage() {
    const input = document.getElementById('chatInput');
    const text = input.value.trim();
    if (!text || !this.currentRoomId) return;
    if (this.ws?.readyState === 1) {
      this.ws.send(JSON.stringify({ type: 'message', content: text }));
    } else {
      await API.post(`/api/chat/rooms/${this.currentRoomId}/messages`, { content: text });
      await this.loadMessages();
    }
    input.value = '';
  },

  escape(s) {
    const d = document.createElement('div');
    d.textContent = s || '';
    return d.innerHTML;
  },
};

document.addEventListener('DOMContentLoaded', () => ChatApp.init());
