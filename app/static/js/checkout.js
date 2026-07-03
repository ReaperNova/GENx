/* ═══════════════════════════════════════════
   GenX — checkout.js
   Coupon AJAX validation + Razorpay payment flow
═══════════════════════════════════════════ */

// ── Coupon application ────────────────────
const couponInput  = document.getElementById("coupon-code");
const couponBtn    = document.getElementById("apply-coupon-btn");
const couponTick   = document.getElementById("coupon-tick");
const couponMsg    = document.getElementById("coupon-msg");
const discountRow  = document.getElementById("discount-row");
const discountAmt  = document.getElementById("discount-amount");
const totalDisplay = document.getElementById("total-display");
const hiddenCoupon = document.getElementById("applied-coupon");

let appliedDiscount = 0;

if (couponBtn) {
  couponBtn.addEventListener("click", applyCoupon);
  couponInput?.addEventListener("keydown", (e) => {
    if (e.key === "Enter") { e.preventDefault(); applyCoupon(); }
  });
}

async function applyCoupon() {
  const code = couponInput?.value.trim().toUpperCase();
  if (!code) return;

  couponBtn.disabled = true;
  couponBtn.textContent = "Checking…";

  const subtotal = parseFloat(document.getElementById("cart-subtotal")?.dataset.subtotal || 0);

  try {
    const res = await fetch("/checkout/apply-coupon", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code, subtotal }),
    });
    const data = await res.json();

    if (data.valid) {
      // Show animated tick
      couponTick?.classList.add("show");
      couponMsg.textContent  = data.message;
      couponMsg.className    = "coupon-msg success";
      appliedDiscount        = data.discount;
      hiddenCoupon.value     = code;

      // Update totals
      discountRow?.classList.remove("hidden");
      discountAmt.textContent = `- ₹${data.discount.toLocaleString("en-IN")}`;
      totalDisplay.textContent = `₹${data.new_total.toLocaleString("en-IN")}`;

      // Bounce animation on total
      gsap.fromTo(totalDisplay, { scale: 1.15 }, { scale: 1, duration: 0.4, ease: "back.out(2)" });
    } else {
      couponTick?.classList.remove("show");
      couponMsg.textContent = data.message;
      couponMsg.className   = "coupon-msg error";
      hiddenCoupon.value    = "";
      appliedDiscount       = 0;
    }
  } catch (err) {
    couponMsg.textContent = "Network error. Please try again.";
    couponMsg.className   = "coupon-msg error";
  } finally {
    couponBtn.disabled = false;
    couponBtn.textContent = "Apply";
  }
}

// ── Razorpay payment flow ─────────────────
const payBtn = document.getElementById("pay-btn");

if (payBtn) {
  payBtn.addEventListener("click", initiatePayment);
}

async function initiatePayment() {
  // Validate form first
  const form = document.getElementById("checkout-form");
  if (!form.checkValidity()) {
    form.reportValidity();
    return;
  }

  payBtn.disabled = true;
  payBtn.innerHTML = `<span class="spinner"></span> Processing…`;

  // Collect form data
  const formData = new FormData(form);
  const cartItems = Alpine.store("cart").items;

  if (!cartItems.length) {
    showToast("Your cart is empty.", "error");
    payBtn.disabled = false;
    payBtn.textContent = "Pay Now";
    return;
  }

  formData.append("cart_items", JSON.stringify(cartItems));

  try {
    const res = await fetch("/checkout/create-order", {
      method: "POST",
      body: formData,
    });
    const data = await res.json();

    if (!data.razorpay_order_id) {
      throw new Error(data.error || "Failed to create order.");
    }

    // Open Razorpay popup
    const options = {
      key: data.razorpay_key,
      amount: data.amount,
      currency: "INR",
      name: data.brand_name,
      description: "Order #" + data.order_id,
      order_id: data.razorpay_order_id,
      prefill: {
        name:    formData.get("name"),
        email:   formData.get("email"),
        contact: formData.get("phone"),
      },
      theme: { color: "#e8ff4a" },
      modal: {
        ondismiss: () => {
          showToast("Payment cancelled.", "error");
          payBtn.disabled = false;
          payBtn.textContent = "Pay Now";
        },
      },
      handler: async function (response) {
        // Verify payment on server
        try {
          const verifyRes = await fetch("/checkout/verify", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              razorpay_payment_id: response.razorpay_payment_id,
              razorpay_order_id:   response.razorpay_order_id,
              razorpay_signature:  response.razorpay_signature,
              internal_order_id:   data.order_id,
            }),
          });
          const verifyData = await verifyRes.json();

          if (verifyData.success) {
            Alpine.store("cart").clear();
            window.location.href = `/orders/confirmation/${verifyData.order_id}`;
          } else {
            showToast("Payment verification failed. Contact support.", "error");
            payBtn.disabled = false;
            payBtn.textContent = "Pay Now";
          }
        } catch (e) {
          showToast("Verification error: " + e.message, "error");
        }
      },
    };

    const rzp = new Razorpay(options);
    rzp.open();
  } catch (err) {
    showToast(err.message, "error");
    payBtn.disabled = false;
    payBtn.textContent = "Pay Now";
  }
}
