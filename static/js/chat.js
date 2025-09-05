let websocket = null;
let currentNickname = '';

function connectToChat() {
  const nickInput = document.getElementById('nickname-input');
  currentNickname = (nickInput.value || '').trim();
  if (!currentNickname) {
    alert('Пожалуйста, введите никнейм');
    return;
  }

  try {
    const scheme = location.protocol === 'https:' ? 'wss' : 'ws';
    websocket = new WebSocket(`${scheme}://${location.host}/ws/anon-chat`);

    websocket.onopen = () => {
      websocket.send(JSON.stringify({ nickname: currentNickname }));
      document.getElementById('username-form').style.display = 'none';
      document.getElementById('message-form').style.display = 'block';
    };

    websocket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        displayMessage(message);
      } catch (e) {
        console.error('Bad message:', e);
      }
    };

    websocket.onclose = () => {
      document.getElementById('username-form').style.display = 'block';
      document.getElementById('message-form').style.display = 'none';
      alert('Соединение закрыто');
    };

    websocket.onerror = (err) => {
      console.error('WebSocket error:', err);
      alert('Ошибка соединения');
    };
  } catch (error) {
    console.error('Connection error:', error);
    alert('Не удалось подключиться к чату');
  }
}

function sendMessage() {
  const messageInput = document.getElementById('message-input');
  const text = (messageInput.value || '').trim();
  if (!text || !websocket || websocket.readyState !== WebSocket.OPEN) return;

  try {
    websocket.send(JSON.stringify({ text }));
    messageInput.value = '';
  } catch (error) {
    console.error('Send error:', error);
  }
}

// безопасный вывод без innerHTML (чтобы не словить XSS)
function displayMessage(message) {
  const wrap = document.getElementById('chat-messages');
  const row = document.createElement('div');
  row.className = `message ${message.type}`;

  const ts = document.createElement('span');
  ts.className = 'timestamp';
  const when = message.timestamp ? new Date(message.timestamp).toLocaleTimeString() : '';
  ts.textContent = when ? `[${when}] ` : '';
  row.appendChild(ts);

  if (message.type === 'message') {
    const nick = document.createElement('span');
    nick.className = 'nickname';
    const strong = document.createElement('strong');
    strong.textContent = message.nickname ? `${message.nickname}:` : 'Гость:';
    nick.appendChild(strong);
    nick.insertAdjacentText('beforeend', ' ');
    row.appendChild(nick);

    const txt = document.createElement('span');
    txt.className = 'text';
    txt.textContent = message.text || '';
    row.appendChild(txt);
  } else {
    const sys = document.createElement('span');
    sys.className = 'system-text';
    sys.textContent = message.text || '';
    row.appendChild(sys);
  }

  wrap.appendChild(row);
  wrap.scrollTop = wrap.scrollHeight;
}

function bindUI() {
  const nickEl = document.getElementById('nickname-input');
  const msgEl  = document.getElementById('message-input');

  nickEl?.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') connectToChat();
  });

  msgEl?.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
  });

  // если есть кнопки — привяжем
  document.getElementById('join-btn')?.addEventListener('click', connectToChat);
  document.getElementById('send-btn')?.addEventListener('click', sendMessage);
}

document.addEventListener('DOMContentLoaded', bindUI);
