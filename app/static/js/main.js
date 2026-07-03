/* ═══════════════════════════════════════════
   GenX — main.js
   GSAP animations: page transitions, navbar,
   hero text, scroll-triggered reveals
═══════════════════════════════════════════ */

// ── Register GSAP plugins ────────────────
gsap.registerPlugin(ScrollTrigger);

// ── Page transition overlay ──────────────
const pageTransition = document.getElementById("page-transition");

function runPageTransitionIn() {
  gsap.fromTo(
    "#page-transition",
    { scaleY: 0, transformOrigin: "bottom" },
    { scaleY: 1, duration: 0.5, ease: "power4.inOut" }
  );
}

function runPageTransitionOut() {
  gsap.fromTo(
    "#page-transition",
    { scaleY: 1, transformOrigin: "top" },
    { scaleY: 0, duration: 0.5, ease: "power4.inOut", delay: 0.1 }
  );
}

window.addEventListener("load", runPageTransitionOut);

// Intercept nav link clicks for smooth transitions
document.querySelectorAll("a[data-transition]").forEach((link) => {
  link.addEventListener("click", (e) => {
    const href = link.getAttribute("href");
    if (!href || href.startsWith("#") || href.startsWith("mailto:")) return;
    e.preventDefault();
    runPageTransitionIn();
    setTimeout(() => { window.location.href = href; }, 600);
  });
});

// ── Navbar scroll behaviour ──────────────
const navbar = document.getElementById("navbar");
if (navbar) {
  window.addEventListener("scroll", () => {
    if (window.scrollY > 60) {
      navbar.classList.add("scrolled");
    } else {
      navbar.classList.remove("scrolled");
    }
  }, { passive: true });
}

// ── Hero text animation ──────────────────
const heroTitle = document.querySelector(".hero-title");
if (heroTitle) {
  const spans = heroTitle.querySelectorAll("span");
  gsap.fromTo(
    spans,
    { y: "100%", opacity: 0 },
    {
      y: "0%",
      opacity: 1,
      duration: 1,
      stagger: 0.1,
      ease: "power4.out",
      delay: 0.3,
    }
  );

  // Subtitle + CTA
  gsap.fromTo(
    ".hero-subtitle, .hero-cta",
    { y: 30, opacity: 0 },
    { y: 0, opacity: 1, duration: 0.8, stagger: 0.15, ease: "power3.out", delay: 0.8 }
  );
}

// ── Scroll-triggered reveals ─────────────
function initScrollAnimations() {
  // Fade-up elements
  gsap.utils.toArray(".fade-up").forEach((el) => {
    gsap.fromTo(
      el,
      { y: 50, opacity: 0 },
      {
        y: 0,
        opacity: 1,
        duration: 0.8,
        ease: "power3.out",
        scrollTrigger: {
          trigger: el,
          start: "top 88%",
          toggleActions: "play none none none",
        },
      }
    );
  });

  // Fade-left
  gsap.utils.toArray(".fade-left").forEach((el) => {
    gsap.fromTo(
      el,
      { x: -50, opacity: 0 },
      {
        x: 0,
        opacity: 1,
        duration: 0.8,
        ease: "power3.out",
        scrollTrigger: { trigger: el, start: "top 88%" },
      }
    );
  });

  // Fade-right
  gsap.utils.toArray(".fade-right").forEach((el) => {
    gsap.fromTo(
      el,
      { x: 50, opacity: 0 },
      {
        x: 0,
        opacity: 1,
        duration: 0.8,
        ease: "power3.out",
        scrollTrigger: { trigger: el, start: "top 88%" },
      }
    );
  });

  // Staggered product cards
  gsap.utils.toArray(".product-card-group").forEach((group) => {
    const cards = group.querySelectorAll(".product-card");
    gsap.fromTo(
      cards,
      { y: 60, opacity: 0 },
      {
        y: 0,
        opacity: 1,
        duration: 0.6,
        stagger: 0.08,
        ease: "power3.out",
        scrollTrigger: { trigger: group, start: "top 85%" },
      }
    );
  });

  // Section titles
  gsap.utils.toArray(".section-title").forEach((title) => {
    gsap.fromTo(
      title,
      { y: 40, opacity: 0 },
      {
        y: 0,
        opacity: 1,
        duration: 0.9,
        ease: "power4.out",
        scrollTrigger: { trigger: title, start: "top 90%" },
      }
    );
  });
}

document.addEventListener("DOMContentLoaded", initScrollAnimations);

// ── Toast notification system ─────────────
window.showToast = function (message, type = "success") {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <span>${type === "success" ? "✓" : "✕"}</span>
    <span>${message}</span>
  `;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.animation = "slideOutRight 0.3s ease forwards";
    setTimeout(() => toast.remove(), 300);
  }, 3500);
};

// ── Product image gallery (detail page) ──
window.switchImage = function (url, thumbEl) {
  const mainImg = document.querySelector(".product-main-img img");
  if (!mainImg) return;

  gsap.to(mainImg, {
    opacity: 0,
    scale: 0.97,
    duration: 0.2,
    onComplete: () => {
      mainImg.src = url;
      gsap.to(mainImg, { opacity: 1, scale: 1, duration: 0.3 });
    },
  });

  document.querySelectorAll(".thumbnail").forEach((t) => t.classList.remove("active"));
  if (thumbEl) thumbEl.classList.add("active");
};

// ── Size picker ───────────────────────────
document.querySelectorAll(".size-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".size-btn").forEach((b) => b.classList.remove("selected"));
    btn.classList.add("selected");
    const sizeInput = document.getElementById("selected-size");
    if (sizeInput) sizeInput.value = btn.dataset.size;

    // Micro bounce
    gsap.fromTo(btn, { scale: 0.9 }, { scale: 1, duration: 0.3, ease: "back.out(2)" });
  });
});

// ── Star picker (review form) ─────────────
const starPicks = document.querySelectorAll(".star-pick");
if (starPicks.length) {
  starPicks.forEach((star, index) => {
    star.addEventListener("mouseenter", () => {
      starPicks.forEach((s, i) => {
        s.classList.toggle("active", i <= index);
        s.textContent = "★";
      });
    });
    star.addEventListener("click", () => {
      const ratingInput = document.getElementById("star-rating-input");
      if (ratingInput) ratingInput.value = index + 1;
    });
  });

  document.querySelector(".star-picker")?.addEventListener("mouseleave", () => {
    const val = parseInt(document.getElementById("star-rating-input")?.value || 0);
    starPicks.forEach((s, i) => {
      s.classList.toggle("active", i < val);
    });
  });
}
