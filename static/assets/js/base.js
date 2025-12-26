(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);

  // =========================
  // Live Time: الوقت | الهجري | الميلادي
  // =========================
  function formatLiveArabic(d) {
    // ✅ الوقت بالثواني (مع ص/م)
    const time = new Intl.DateTimeFormat("ar-SA", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: true,
      // timeZone: "Asia/Riyadh",
    }).format(d);

    // ✅ التاريخ الهجري (مع اسم اليوم + هـ)
    const hijri = new Intl.DateTimeFormat("ar-SA-u-ca-islamic", {
      weekday: "long",
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      timeZone: "Asia/Riyadh",
    }).format(d);

    // ✅ التاريخ الميلادي (مع اسم اليوم + م)
    const greg = new Intl.DateTimeFormat("ar-SA-u-ca-gregory", {
      weekday: "long",
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      timeZone: "Asia/Riyadh",
    }).format(d);

    // المطلوب: الوقت ثم | الهجري ثم | الميلادي
    return `الوقت الآن: ${time} | ${hijri}  | ${greg} م`;
  }

  function initLiveTime(root) {
    const liveEl = root.querySelector("#liveTime");
    if (!liveEl) return;

    // حماية: لا تشغل أكثر من مؤقت
    if (document.documentElement.dataset.thqafClockBound === "1") return;
    document.documentElement.dataset.thqafClockBound = "1";

    const update = () => {
      liveEl.textContent = formatLiveArabic(new Date());
    };

    update();
    const timer = setInterval(update, 1000);

    window.addEventListener("beforeunload", () => clearInterval(timer));
  }

  // =========================
  // Dropdowns
  // =========================
  function setupDropdown(dropId, btnId) {
    const drop = $(dropId);
    const btn = $(btnId);
    if (!drop || !btn) return;

    const close = () => {
      drop.classList.remove("open");
      btn.setAttribute("aria-expanded", "false");
    };

    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const open = drop.classList.toggle("open");
      btn.setAttribute("aria-expanded", open ? "true" : "false");
    });

    // لا تغلق عند الضغط داخل القائمة نفسها
    drop.addEventListener("click", (e) => e.stopPropagation());

    // close on outside click
    document.addEventListener("click", () => close());

    // close on ESC
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") close();
    });
  }

  // =========================
  // Mobile Menu
  // =========================
  function setupMobileMenu() {
    const burger = $("hamburger");
    const menu = $("menu");
    if (!burger || !menu) return;

    burger.addEventListener("click", (e) => {
      e.stopPropagation();
      const open = menu.classList.toggle("open");
      burger.setAttribute("aria-expanded", open ? "true" : "false");
    });

    // منع إغلاق القائمة عند الضغط داخلها
    menu.addEventListener("click", (e) => e.stopPropagation());

    document.addEventListener("click", () => {
      menu.classList.remove("open");
      burger.setAttribute("aria-expanded", "false");
    });

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") {
        menu.classList.remove("open");
        burger.setAttribute("aria-expanded", "false");
      }
    });
  }

  // =========================
  // Admin Modal
  // =========================
  function setupAdminModal() {
    const modal = $("adminModal");
    const openBtn = $("loginBtn");
    const closeBtn = $("closeAdminModal");
    const cancelBtn = $("cancelAdminModal");

    if (!modal || !openBtn) return;

    const open = () => {
      modal.classList.add("active");
      modal.setAttribute("aria-hidden", "false");
      const phone = $("adminPhone");
      if (phone) phone.focus();
    };

    const close = () => {
      modal.classList.remove("active");
      modal.setAttribute("aria-hidden", "true");
      openBtn.focus();
    };

    openBtn.addEventListener("click", (e) => {
      e.preventDefault();
      open();
    });

    if (closeBtn) closeBtn.addEventListener("click", close);
    if (cancelBtn) cancelBtn.addEventListener("click", close);

    modal.addEventListener("click", (e) => {
      if (e.target === modal) close();
    });

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && modal.classList.contains("active")) close();
    });

    const submit = $("adminLoginSubmit");
    if (submit) {
      submit.addEventListener("click", () => {
        // Placeholder: لاحقاً نربطه بصفحة/endpoint تسجيل الدخول الحقيقي
        close();
      });
    }
  }

  // =========================
  // DOM Ready
  // =========================
  document.addEventListener("DOMContentLoaded", () => {
    initLiveTime(document);
    setupDropdown("coursesDropdown", "coursesBtn");
    setupDropdown("supportDropdown", "supportBtn");
    setupMobileMenu();
    setupAdminModal();
  });
})();
