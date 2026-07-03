/* ═══════════════════════════════════════════
   GenX — cart.js
   Alpine.js global cart store + drawer logic.
   Cart state persisted to sessionStorage.
═══════════════════════════════════════════ */

document.addEventListener("alpine:init", () => {
  Alpine.store("cart", {
    open: false,
    items: JSON.parse(sessionStorage.getItem("genx_cart") || "[]"),

    // ── Getters ─────────────────────────
    get count() {
      return this.items.reduce((sum, i) => sum + i.quantity, 0);
    },

    get subtotal() {
      return this.items.reduce((sum, i) => sum + i.price * i.quantity, 0);
    },

    get subtotalFormatted() {
      return "₹" + this.subtotal.toLocaleString("en-IN");
    },

    // ── Actions ──────────────────────────
    add(product) {
      const existing = this.items.find(
        (i) => i.id === product.id && i.size === product.size
      );
      if (existing) {
        existing.quantity = Math.min(existing.quantity + product.quantity, 10);
      } else {
        this.items.push({ ...product });
      }
      this.persist();
      this.openDrawer();
      showToast(`${product.name} added to cart!`, "success");
    },

    remove(productId, size) {
      this.items = this.items.filter(
        (i) => !(i.id === productId && i.size === size)
      );
      this.persist();
    },

    updateQty(productId, size, delta) {
      const item = this.items.find(
        (i) => i.id === productId && i.size === size
      );
      if (!item) return;
      item.quantity = Math.max(1, Math.min(item.quantity + delta, 10));
      this.persist();
    },

    clear() {
      this.items = [];
      this.persist();
    },

    persist() {
      sessionStorage.setItem("genx_cart", JSON.stringify(this.items));
    },

    openDrawer() {
      this.open = true;
      document.body.style.overflow = "hidden";
      const drawer  = document.getElementById("cart-drawer");
      const overlay = document.getElementById("cart-overlay");
      drawer?.classList.add("open");
      overlay?.classList.add("open");
    },

    closeDrawer() {
      this.open = false;
      document.body.style.overflow = "";
      const drawer  = document.getElementById("cart-drawer");
      const overlay = document.getElementById("cart-overlay");
      drawer?.classList.remove("open");
      overlay?.classList.remove("open");
    },

    // Serialise for checkout form hidden field
    toJSON() {
      return JSON.stringify(this.items);
    },
  });
});

// ── Expose for non-Alpine code (e.g. product page) ──
window.addToCart = function (product) {
  Alpine.store("cart").add(product);
};
