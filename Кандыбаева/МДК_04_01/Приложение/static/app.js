const state = { user: null, products: [], cart: [], filters: {}, order: null, items: [], removed: [] };
const $ = (selector) => document.querySelector(selector);
async function api(url, options) {
  const response = await fetch(url, options);
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || 'Ошибка запроса');
  return result;
}
function message(text) { $('#message').textContent = text; }
function cell(row, value) { const td = row.insertCell(); td.textContent = value; return td; }
async function loadOrders() {
  const orders = await api('/api/orders');
  const body = $('#orders'); body.replaceChildren();
  for (const order of orders) {
    const row = body.insertRow();
    cell(row, order.id); cell(row, order.order_date); cell(row, order.full_name);
    const button = document.createElement('button'); button.textContent = 'Открыть';
    button.addEventListener('click', () => openOrder(order).catch(error => message(error.message)));
    cell(row, '').append(button);
  }
}
async function openOrder(order) {
  state.order = order; state.removed = []; state.items = await api('/api/order?id=' + order.id);
  $('#order-title').textContent = 'Заказ № ' + order.id;
  $('#order-date').value = order.order_date;
  const admin = state.user.role === 'Администратор';
  $('#order-date').disabled = !admin; $('#save').hidden = !admin;
  renderItems(); $('#order-dialog').showModal();
}
function renderItems() {
  const body = $('#items'); body.replaceChildren(); let total = 0;
  for (const item of state.items.filter(item => !state.removed.includes(item.id))) {
    const row = body.insertRow();
    for (const value of [item.name, item.size, item.quantity, item.unit_price, item.total]) cell(row, value);
    total += item.total;
    if (state.user.role === 'Администратор') {
      const button = document.createElement('button'); button.type = 'button'; button.textContent = 'Удалить';
      button.addEventListener('click', () => { state.removed.push(item.id); renderItems(); });
      cell(row, '').append(button);
    }
  }
  $('#total').textContent = total + ' ₽';
}
$('#login-form').addEventListener('submit', async event => {
  event.preventDefault();
  try {
    state.user = await api('/api/login?login=' + encodeURIComponent(event.target.login.value));
    $('#current-user').textContent = state.user.full_name + ' — ' + state.user.role;
    $('#orders-section').hidden = !['Менеджер', 'Администратор'].includes(state.user.role);
    if (!$('#orders-section').hidden) await loadOrders();
    message('');
  } catch (error) { message(error.message); }
});
$('#logout').addEventListener('click', () => { state.user = null; $('#orders-section').hidden = true; $('#current-user').textContent = 'Гость'; });
$('#close').addEventListener('click', () => $('#order-dialog').close());
$('#order-form').addEventListener('submit', async event => {
  event.preventDefault();
  try {
    await api('/api/order/update', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id: state.order.id, date: $('#order-date').value, removed: state.removed }) });
    $('#order-dialog').close(); await loadOrders(); message('Изменения сохранены.');
  } catch (error) { message(error.message); }
});
