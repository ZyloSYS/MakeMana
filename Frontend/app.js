const CART_KEY = "makemana_cart";

const moneyToNumber = (value) => {
  const normalized = String(value || "")
    .replace("R$", "")
    .replace(/\./g, "")
    .replace(",", ".")
    .trim();
  return Number(normalized) || 0;
};

const numberToMoney = (value) =>
  value.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });

const readCart = () => {
  try {
    return JSON.parse(localStorage.getItem(CART_KEY)) || [];
  } catch (_error) {
    return [];
  }
};

const writeCart = (items) => {
  localStorage.setItem(CART_KEY, JSON.stringify(items));
};

const openCart = () => {
  document.body.classList.add("cart-is-open");
  document.querySelector(".cart-drawer")?.setAttribute("aria-hidden", "false");
};

const closeCart = () => {
  document.body.classList.remove("cart-is-open");
  document.querySelector(".cart-drawer")?.setAttribute("aria-hidden", "true");
};

const renderCart = () => {
  const items = readCart();
  const list = document.querySelector("[data-cart-items]");
  const empty = document.querySelector("[data-cart-empty]");
  const count = document.querySelector("[data-cart-count]");
  const total = document.querySelector("[data-cart-total]");
  const checkout = document.querySelector("[data-cart-checkout]");

  if (!list || !empty || !count || !total || !checkout) return;

  list.innerHTML = "";
  count.textContent = String(items.length);
  empty.hidden = items.length > 0;

  items.forEach((item) => {
    const row = document.createElement("article");
    row.className = "cart-item";
    row.innerHTML = `
      <img src="${item.image}" alt="">
      <div>
        <h3>${item.name}</h3>
        <p>${item.price}</p>
      </div>
      <button type="button" data-remove-cart="${item.id}" aria-label="Remover ${item.name}">×</button>
    `;
    list.appendChild(row);
  });

  const cartTotal = items.reduce((sum, item) => sum + moneyToNumber(item.price), 0);
  total.textContent = numberToMoney(cartTotal);
  checkout.href = items[0]?.url || "/pedido";
};

const setupCart = () => {
  renderCart();

  document.addEventListener("click", (event) => {
    const addButton = event.target.closest("[data-add-cart]");
    if (addButton) {
      const item = {
        id: addButton.dataset.id,
        name: addButton.dataset.name,
        price: addButton.dataset.price,
        image: addButton.dataset.image,
        url: addButton.dataset.url,
      };
      const current = readCart().filter((cartItem) => cartItem.id !== item.id);
      writeCart([...current, item]);
      renderCart();
      openCart();
      return;
    }

    const removeButton = event.target.closest("[data-remove-cart]");
    if (removeButton) {
      writeCart(readCart().filter((item) => item.id !== removeButton.dataset.removeCart));
      renderCart();
      return;
    }

    if (event.target.closest("[data-cart-open]")) {
      openCart();
      return;
    }

    if (event.target.closest("[data-cart-close]")) {
      closeCart();
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeCart();
  });
};

const setupFilters = () => {
  const grid = document.querySelector("[data-products-grid]");
  const cards = [...document.querySelectorAll(".product-filter-card")];
  const filterForm = document.querySelector("[data-product-filters]");
  const sortSelect = document.querySelector("[data-sort-products]");
  const count = document.querySelector("[data-product-count]");
  const empty = document.querySelector("[data-products-empty]");
  const search = document.querySelector(".site-search");

  if (!cards.length) return;

  const params = new URLSearchParams(window.location.search);
  const initialCategory = params.get("categoria");
  const initialSearch = params.get("q");
  if (filterForm && initialCategory) {
    const field = filterForm.querySelector(`[name="categoria"][value="${initialCategory}"]`);
    if (field) field.checked = true;
  }
  if (search && initialSearch && !search.value) {
    search.value = initialSearch;
  }

  const applyFilters = () => {
    const selectedCategories = filterForm
      ? [...filterForm.querySelectorAll('[name="categoria"]:checked')].map((field) => field.value)
      : [];
    const priceLimit = filterForm?.querySelector('[name="preco"]:checked')?.value || "";
    const term = (search?.value || "").trim().toLowerCase();
    let visible = 0;

    cards.forEach((card) => {
      const matchesCategory =
        selectedCategories.length === 0 ||
        selectedCategories.includes(card.dataset.category) ||
        selectedCategories.includes(card.dataset.line);
      const matchesPrice = !priceLimit || Number(card.dataset.price) <= Number(priceLimit);
      const searchableText = card.dataset.search || card.dataset.name || "";
      const matchesSearch = !term || searchableText.includes(term);
      const show = matchesCategory && matchesPrice && matchesSearch;
      if (show) {
        card.hidden = false;
      }
      card.classList.toggle("is-filtered-out", !show);
      window.setTimeout(() => {
        card.hidden = !show;
      }, show ? 0 : 180);
      if (show) visible += 1;
    });

    if (count) count.textContent = String(visible);
    if (empty) empty.hidden = visible !== 0;
  };

  const applySort = () => {
    if (!grid || !sortSelect) return;
    const sortedCards = [...cards].sort((a, b) => {
      if (sortSelect.value === "menor-preco") return Number(a.dataset.price) - Number(b.dataset.price);
      if (sortSelect.value === "maior-preco") return Number(b.dataset.price) - Number(a.dataset.price);
      if (sortSelect.value === "az") return a.dataset.name.localeCompare(b.dataset.name);
      return 0;
    });
    sortedCards.forEach((card) => grid.appendChild(card));
  };

  filterForm?.addEventListener("change", applyFilters);
  sortSelect?.addEventListener("change", () => {
    applySort();
    applyFilters();
  });
  search?.addEventListener("input", applyFilters);

  applySort();
  applyFilters();
};

const setupEmergencyExit = () => {
  document.addEventListener("click", (event) => {
    const button = event.target.closest("[data-emergency-exit]");
    if (!button) return;
    sessionStorage.setItem("makemana_return_hint", String(Date.now()));
    window.location.assign("https://www.google.com");
  });

  const chip = document.querySelector("[data-return-chip]");
  const lastExit = Number(sessionStorage.getItem("makemana_return_hint") || 0);
  if (chip && lastExit && Date.now() - lastExit < 15 * 60 * 1000) {
    chip.classList.add("is-visible");
    setTimeout(() => chip.classList.remove("is-visible"), 8000);
  }
};

const setupReveals = () => {
  const elements = document.querySelectorAll(".reveal-on-scroll");
  if (!("IntersectionObserver" in window)) {
    elements.forEach((element) => element.classList.add("is-visible"));
    return;
  }

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.16 }
  );

  elements.forEach((element) => observer.observe(element));
};

document.addEventListener("DOMContentLoaded", () => {
  setupCart();
  setupFilters();
  setupEmergencyExit();
  setupReveals();
});
