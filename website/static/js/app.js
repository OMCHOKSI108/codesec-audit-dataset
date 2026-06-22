document.addEventListener("DOMContentLoaded", function () {
  // Flash message auto-dismiss
  document.querySelectorAll(".flash").forEach(function (el) {
    setTimeout(function () { el.style.opacity = "0"; setTimeout(function () { el.remove(); }, 300); }, 4000);
  });
});
