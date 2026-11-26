const CART_KEY = 'milkyLeafCart';

function money(value) {
  return new Intl.NumberFormat('vi-VN', { maximumFractionDigits: 0 }).format(Number(value) || 0) + 'đ';
}

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, (char) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  })[char]);
}

function readCart() {
  try {
    const cart = JSON.parse(localStorage.getItem(CART_KEY) || '[]');
    return Array.isArray(cart) ? cart : [];
  } catch (_) {
    return [];
  }
}

function writeCart(cart) {
  localStorage.setItem(CART_KEY, JSON.stringify(cart));
  updateCartCount();
}

function updateCartCount() {
  const count = readCart().reduce((sum, item) => sum + (Number(item.quantity) || 0), 0);
  document.querySelectorAll('.cart-count').forEach((node) => { node.textContent = String(count); });
}

function addToCart(product, quantity = 1) {
  const cart = readCart();
  const existing = cart.find((item) => Number(item.product_id) === Number(product.id));
  const nextQuantity = (existing ? Number(existing.quantity) : 0) + quantity;
  if (nextQuantity > product.stock) {
    alert('Số lượng vượt quá tồn kho hiện tại.');
    return;
  }
  if (existing) existing.quantity = nextQuantity;
  else cart.push({ product_id: product.id, quantity });
  writeCart(cart);
  alert('Đã thêm sản phẩm vào giỏ hàng.');
}

function productCard(product) {
  const card = document.createElement('article');
  card.className = 'product-card';
  card.innerHTML = `<a href="/client/product/${Number(product.id)}" class="product-image-link" aria-label="Xem ${escapeHtml(product.name)}"><div class="product-image">🧋</div></a>
    <h3><a href="/client/product/${Number(product.id)}">${escapeHtml(product.name)}</a></h3>
    <p class="price">${money(product.price)}</p><p class="stock">${product.stock > 0 ? `Còn ${Number(product.stock)} sản phẩm` : 'Tạm hết hàng'}</p>
    <div class="card-actions"><a class="btn btn-secondary" href="/client/product/${Number(product.id)}">Chi tiết</a><button class="btn btn-small" type="button" ${product.stock <= 0 ? 'disabled' : ''}>Thêm vào giỏ</button></div>`;
  card.querySelector('button').addEventListener('click', () => addToCart(product));
  return card;
}

async function getProducts(params = '') {
  const response = await fetch(`/api/products${params}`, { credentials: 'same-origin' });
  const data = await response.json();
  if (!response.ok || !data.ok) throw new Error(data.error || 'Không thể tải sản phẩm.');
  return data.products;
}

async function loadProductList() {
  const container = document.querySelector('[data-product-list]');
  const featured = document.querySelector('[data-featured-products]');
  const filter = document.querySelector('[data-product-filter]');
  if (!container && !featured) return;

  const render = async (params = '') => {
    const target = container || featured;
    target.innerHTML = '<p class="muted">Đang tải sản phẩm…</p>';
    try {
      const products = await getProducts(params);
      if (!products.length) {
        target.innerHTML = '<p class="empty-state">Không tìm thấy sản phẩm phù hợp.</p>';
        return;
      }
      target.replaceChildren(...(container ? products : products.slice(0, 3)).map(productCard));
    } catch (error) {
      target.innerHTML = `<p class="error-message">${escapeHtml(error.message)}</p>`;
    }
  };

  if (filter) {
    const params = new URLSearchParams(window.location.search);
    ['q', 'min_price', 'max_price'].forEach((key) => { if (params.has(key)) filter.elements[key].value = params.get(key); });
    filter.addEventListener('submit', (event) => {
      event.preventDefault();
      const values = new URLSearchParams(new FormData(filter));
      [...values.keys()].forEach((key) => { if (!values.get(key)) values.delete(key); });
      const search = values.toString();
      history.replaceState(null, '', search ? `?${search}` : window.location.pathname);
      render(search ? `?${search}` : '');
    });
    render(window.location.search);
  } else {
    render();
  }
}

async function loadProductDetail() {
  const container = document.querySelector('[data-product-detail]');
  if (!container) return;
  try {
    const response = await fetch(`/api/products/${Number(container.dataset.productDetail)}`);
    const data = await response.json();
    if (!response.ok || !data.ok) throw new Error(data.error || 'Không tìm thấy sản phẩm.');
    const product = data.product;
    container.innerHTML = `<article class="product-detail"><div class="product-image detail-image">🧋</div><div><p class="eyebrow">Milky Leaf Tea House</p><h1>${escapeHtml(product.name)}</h1><p class="price detail-price">${money(product.price)}</p><p>${escapeHtml(product.description || 'Sản phẩm tươi ngon được pha chế tại Milky Leaf.')}</p><p class="stock">${product.stock > 0 ? `Còn ${Number(product.stock)} sản phẩm` : 'Tạm hết hàng'}</p><label class="quantity-label">Số lượng<input type="number" min="1" max="${Number(product.stock)}" value="1" data-detail-quantity ${product.stock <= 0 ? 'disabled' : ''}></label><button class="btn btn-primary" type="button" data-detail-add ${product.stock <= 0 ? 'disabled' : ''}>Thêm vào giỏ hàng</button></div></article>`;
    container.querySelector('[data-detail-add]').addEventListener('click', () => {
      const quantity = Number(container.querySelector('[data-detail-quantity]').value);
      if (!Number.isInteger(quantity) || quantity < 1 || quantity > product.stock) return alert('Vui lòng chọn số lượng hợp lệ.');
      addToCart(product, quantity);
    });
  } catch (error) {
    container.innerHTML = `<p class="error-message">${escapeHtml(error.message)} <a href="/client/storeproduct.html">Quay lại danh sách sản phẩm</a></p>`;
  }
}

async function loadCart() {
  const container = document.querySelector('[data-cart-items]');
  if (!container) return;
  const cart = readCart();
  if (!cart.length) {
    container.innerHTML = '<p class="empty-state">Giỏ hàng đang trống. <a href="/client/storeproduct.html">Khám phá sản phẩm</a></p>';
    document.querySelector('[data-cart-total]').textContent = money(0);
    return;
  }
  try {
    const products = await Promise.all(cart.map(async (item) => {
      const response = await fetch(`/api/products/${Number(item.product_id)}`);
      const data = await response.json();
      return response.ok && data.ok ? { ...data.product, quantity: Number(item.quantity) } : null;
    }));
    const available = products.filter(Boolean);
    if (available.length !== cart.length) writeCart(cart.filter((item) => available.some((p) => p.id === Number(item.product_id))));
    let total = 0;
    container.replaceChildren(...available.map((product) => {
      const lineTotal = product.price * product.quantity;
      total += lineTotal;
      const row = document.createElement('article');
      row.className = 'cart-item';
      row.innerHTML = `<div class="cart-product-icon">🧋</div><div class="cart-product-info"><h3>${escapeHtml(product.name)}</h3><p class="price">${money(product.price)} / ly</p><p class="stock">${product.stock < product.quantity ? `Chỉ còn ${product.stock} sản phẩm` : 'Còn hàng'}</p></div><label class="quantity-label">SL<input type="number" min="1" max="99" value="${product.quantity}" aria-label="Số lượng ${escapeHtml(product.name)}"></label><strong>${money(lineTotal)}</strong><button class="remove-button" type="button" aria-label="Xóa ${escapeHtml(product.name)}">Xóa</button>`;
      const input = row.querySelector('input');
      input.addEventListener('change', () => {
        const quantity = Math.min(99, Math.max(1, Number(input.value) || 1));
        const updated = readCart().map((item) => Number(item.product_id) === product.id ? { ...item, quantity } : item);
        writeCart(updated);
        loadCart();
      });
      row.querySelector('.remove-button').addEventListener('click', () => {
        writeCart(readCart().filter((item) => Number(item.product_id) !== product.id));
        loadCart();
      });
      return row;
    }));
    document.querySelector('[data-cart-total]').textContent = money(total);
  } catch (_) {
    container.innerHTML = '<p class="error-message">Không thể tải giỏ hàng. Vui lòng tải lại trang.</p>';
  }
}

function setupOrderForm() {
  const form = document.querySelector('[data-order-form]');
  if (!form) return;
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const message = document.querySelector('[data-order-message]');
    const cart = readCart();
    if (!cart.length) {
      message.textContent = 'Giỏ hàng đang trống.';
      message.className = 'status-message error-message';
      return;
    }
    const button = form.querySelector('button[type="submit"]');
    button.disabled = true;
    message.textContent = 'Đang gửi đơn hàng…';
    message.className = 'status-message';
    const payload = Object.fromEntries(new FormData(form));
    payload.items = cart.map((item) => ({ product_id: Number(item.product_id), quantity: Number(item.quantity) }));
    try {
      const response = await fetch('/api/client/orders', {
        method: 'POST', credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
      });
      const data = await response.json();
      if (response.status === 401) {
        alert('Vui lòng đăng nhập bằng tài khoản khách hàng để đặt hàng.');
        window.location.href = '/client/login.html';
        return;
      }
      if (!response.ok || !data.ok) throw new Error(data.error || 'Không thể đặt hàng.');
      localStorage.removeItem(CART_KEY);
      updateCartCount();
      message.className = 'status-message success-message';
      message.textContent = `Đặt hàng thành công! Mã đơn #${data.order_id} — tổng tiền ${money(data.total)}.`;
      form.reset();
      await loadCart();
    } catch (error) {
      message.className = 'status-message error-message';
      message.textContent = error.message;
    } finally {
      button.disabled = false;
    }
  });
}

async function loadOrderHistory() {
  const list = document.querySelector('[data-order-list]');
  const message = document.querySelector('[data-orders-message]');
  if (!list) return;
  try {
    const response = await fetch('/api/client/orders', { credentials: 'same-origin' });
    const data = await response.json();
    if (response.status === 401) {
      message.innerHTML = 'Vui lòng <a href="/client/login.html">đăng nhập</a> để xem lịch sử đơn hàng.';
      return;
    }
    if (!response.ok || !data.ok) throw new Error(data.error || 'Không thể tải lịch sử đơn hàng.');
    if (!data.orders.length) {
      message.textContent = 'Bạn chưa có đơn hàng nào.';
      return;
    }
    message.textContent = '';
    list.replaceChildren(...data.orders.map((order) => {
      const card = document.createElement('article');
      card.className = 'order-card';
      const items = order.items.map((item) => `<li>${escapeHtml(item.name || `Sản phẩm #${item.product_id}`)} × ${Number(item.quantity)} — ${money(item.price * item.quantity)}</li>`).join('');
      card.innerHTML = `<div class="order-heading"><h2>Đơn hàng #${Number(order.id)}</h2><span class="role-badge">${escapeHtml(order.status)}</span></div><p class="muted">${escapeHtml(order.created_at || '')}</p><ul>${items}</ul><p><strong>Tổng cộng: ${money(order.total)}</strong></p><p class="small">Giao đến: ${escapeHtml(order.customer_name)}, ${escapeHtml(order.phone)} — ${escapeHtml(order.delivery_address)}</p>`;
      return card;
    }));
  } catch (error) {
    message.className = 'status-message error-message';
    message.textContent = error.message;
  }
}

async function logout() {
  await fetch('/admin/logout', { method: 'POST', credentials: 'same-origin' });
  window.location.href = '/client/login.html';
}

async function refreshAuthUI() {
  const container = document.querySelector('.auth-actions');
  if (!container) return;
  try {
    const response = await fetch('/admin/me', { credentials: 'same-origin' });
    if (!response.ok) return;
    const data = await response.json();
    const user = data.user;
    const name = document.createElement('span');
    name.className = 'user-name';
    name.textContent = user.username;
    const button = document.createElement('button');
    button.className = 'btn btn-secondary';
    button.type = 'button';
    button.textContent = 'Đăng xuất';
    button.addEventListener('click', logout);
    container.replaceChildren(name, button);
  } catch (_) {
    // Keep the sign-in link visible when the backend is unavailable.
  }
}

document.addEventListener('DOMContentLoaded', () => {
  updateCartCount();
  refreshAuthUI();
  loadProductList();
  loadProductDetail();
  loadCart();
  setupOrderForm();
  loadOrderHistory();
});
