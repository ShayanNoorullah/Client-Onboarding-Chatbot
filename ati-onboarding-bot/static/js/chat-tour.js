function startChatTour() {
  if (localStorage.getItem("ati_tour_done") === "1") return;
  if (typeof window.driver === "undefined") return;

  const driver = window.driver.js.driver;
  const d = driver({
    showProgress: true,
    steps: [
      { element: "#newChatBtn", popover: { title: "Start a project", description: "Create a new onboarding conversation." } },
      { element: "#sessionList", popover: { title: "Your sessions", description: "Resume any previous project from the sidebar." } },
      { element: "#messageInput", popover: { title: "Chat", description: "Answer questions one at a time. Upload files when prompted." } },
      { element: "#fileUploadZone", popover: { title: "Uploads", description: "Share mockups, PDFs, or requirements documents." } },
    ],
    onDestroyed: () => localStorage.setItem("ati_tour_done", "1"),
  });
  d.drive();
}

document.addEventListener("DOMContentLoaded", () => {
  setTimeout(startChatTour, 1200);
});
