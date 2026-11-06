const state = { user: null, events: [], applications: [], register: false, reviewId: null, eventId: null };
const $ = selector => document.querySelector(selector);
const escapeHTML = value => String(value).replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
async function api(url, body) {
  const response = await fetch(url, body ? {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)} : {});
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || 'Ошибка запроса');
  return data;
}
function notify(message) { $('#notice').textContent = message; $('#notice').hidden = !message; }
function show(view) { $('#events-view').hidden = view !== 'events'; $('#applications-view').hidden = view !== 'applications'; notify(''); }
function authMode(register) {
  state.register = register; $('#registration-fields').hidden = !register;
  for (const name of ['email','phone']) $('#auth-form').elements[name].required = register;
  $('#auth-title').textContent = register ? 'Создать аккаунт' : 'Войти в личный кабинет';
  $('#auth-submit').textContent = register ? 'Зарегистрироваться' : 'Войти';
  $('#auth-toggle').textContent = register ? 'Уже есть аккаунт? Войти' : 'Создать аккаунт';
  $('#form-error').textContent = '';
}
function refreshAccount() { $('#account-button').textContent = state.user ? state.user.login + ' · Выйти' : 'Войти'; }
function renderEvents() {
  $('#events').innerHTML = state.events.map(event => `<article class="event"><span class="tag">Конференция</span><h2>${escapeHTML(event.title)}</h2><p>${escapeHTML(event.description)}</p><div class="event-bottom"><div class="event-meta"><span>Дата: ${escapeHTML(event.event_date)}</span><span>Место: ${escapeHTML(event.venue)}</span></div><button class="secondary" data-apply="${event.id}">Подать заявку</button></div></article>`).join('');
}
function renderApplications() {
  const filter = $('#status-filter').value;
  const items = state.applications.filter(item => !filter || String(item.status_id) === filter);
  const admin = state.user && state.user.role === 'admin';
  $('#applications-title').textContent = admin ? 'Все заявки' : 'Мои заявки';
  $('#filter-label').hidden = !admin;
  $('#applications').innerHTML = items.length ? items.map(item => {
    const now = new Date();
    const today = [now.getFullYear(), String(now.getMonth()+1).padStart(2,'0'), String(now.getDate()).padStart(2,'0')].join('-');
    const review = !admin && item.status_id === 3 && item.event_date <= today && !item.review_id;
    return `<article class="event"><span class="tag">${escapeHTML(item.status)}</span><h2>${escapeHTML(item.title)}</h2><p>Дата: ${escapeHTML(item.event_date)} · ${escapeHTML(item.venue)}${admin ? ' · Участник: '+escapeHTML(item.login) : ''}<br>Оплата: ${escapeHTML(item.payment_method)} · Помещение: ${escapeHTML(item.room)}</p><div class="event-bottom">${admin && item.status_id < 3 ? `<button class="primary" data-status="${item.id}">Следующий статус</button>` : ''}${!admin && item.status_id === 1 ? `<button class="secondary" data-cancel="${item.id}">Отменить заявку</button>` : ''}${review ? `<button class="secondary" data-review="${item.id}">Оставить отзыв</button>` : ''}${item.review_id ? '<span>Отзыв отправлен</span>' : ''}</div></article>`;
  }).join('') : '<p>Заявок пока нет.</p>';
}
async function loadApplications() { state.applications = await api('/api/applications'); renderApplications(); }
$('#events-link').addEventListener('click', () => show('events'));
$('#applications-link').addEventListener('click', async () => {
  if (!state.user) { authMode(false); $('#auth-dialog').showModal(); return; }
  try { await loadApplications(); show('applications'); } catch (error) { notify(error.message); }
});
$('#account-button').addEventListener('click', async () => {
  if (!state.user) { authMode(false); $('#auth-dialog').showModal(); return; }
  try { await api('/api/logout', {}); state.user = null; refreshAccount(); show('events'); notify('Вы вышли из системы.'); } catch (error) { notify(error.message); }
});
$('#auth-close').addEventListener('click', () => $('#auth-dialog').close());
$('#auth-toggle').addEventListener('click', () => authMode(!state.register));
$('#auth-form').addEventListener('submit', async event => {
  event.preventDefault(); const data = Object.fromEntries(new FormData(event.currentTarget));
  try {
    if (state.register) { const result = await api('/api/register', data); authMode(false); $('#form-error').textContent = result.message; }
    else { state.user = await api('/api/login', data); refreshAccount(); $('#auth-dialog').close(); notify('Вы вошли в систему.'); event.currentTarget.reset(); }
  } catch (error) { $('#form-error').textContent = error.message; }
});
$('#events').addEventListener('click', async event => {
  const button = event.target.closest('[data-apply]'); if (!button) return;
  if (!state.user) { authMode(false); $('#auth-dialog').showModal(); return; }
  state.eventId = Number(button.dataset.apply); $('#apply-dialog').showModal();
});
$('#apply-close').addEventListener('click', () => $('#apply-dialog').close());
$('#apply-form').addEventListener('submit', async event => {
  event.preventDefault(); const data = Object.fromEntries(new FormData(event.currentTarget)); data.event_id = state.eventId;
  try { const result = await api('/api/apply', data); $('#apply-dialog').close(); notify(result.message); }
  catch (error) { $('#apply-dialog').close(); notify(error.message); }
});
$('#status-filter').addEventListener('change', renderApplications);
$('#applications').addEventListener('click', async event => {
  const status = event.target.closest('[data-status]'); const review = event.target.closest('[data-review]'); const cancel = event.target.closest('[data-cancel]');
  try {
    if (status) { await api('/api/status', {id:Number(status.dataset.status)}); await loadApplications(); notify('Статус обновлён.'); }
    if (cancel) { await api('/api/cancel', {id:Number(cancel.dataset.cancel)}); await loadApplications(); notify('Заявка отменена.'); }
    if (review) { state.reviewId = Number(review.dataset.review); $('#review-dialog').showModal(); }
  } catch (error) { notify(error.message); }
});
$('#review-close').addEventListener('click', () => $('#review-dialog').close());
$('#review-form').addEventListener('submit', async event => {
  event.preventDefault(); const data = Object.fromEntries(new FormData(event.currentTarget)); data.id = state.reviewId;
  try { await api('/api/review', data); $('#review-dialog').close(); event.currentTarget.reset(); await loadApplications(); notify('Отзыв сохранён.'); }
  catch (error) { $('#review-dialog').close(); notify(error.message); }
});
(async () => { try { [state.user,state.events] = await Promise.all([api('/api/me'),api('/api/events')]); refreshAccount(); renderEvents(); } catch (error) { notify(error.message); } })();
