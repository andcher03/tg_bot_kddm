document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".content-read-only form button[type='submit']")
        .forEach((button) => { button.disabled = true; });

    const body = document.body;
    const menuToggle = document.getElementById("mobileMenuToggle");
    const menuClose = document.getElementById("mobileMenuClose");
    const sidebar = document.getElementById("adminSidebar");
    const overlay = document.getElementById("mobileNavOverlay");
    const mobileMedia = window.matchMedia("(max-width: 900px)");

    function setSidebarAvailable(available) {
        sidebar.inert = !available;
        sidebar.setAttribute("aria-hidden", String(!available));
    }

    function openMenu() {
        body.classList.add("mobile-nav-open");
        overlay.hidden = false;
        menuToggle.setAttribute("aria-expanded", "true");
        setSidebarAvailable(true);
        menuClose.focus();
    }

    function closeMenu() {
        body.classList.remove("mobile-nav-open");
        overlay.hidden = true;
        menuToggle.setAttribute("aria-expanded", "false");
        setSidebarAvailable(!mobileMedia.matches);
    }

    if (menuToggle && menuClose && sidebar && overlay) {
        menuToggle.addEventListener("click", openMenu);
        menuClose.addEventListener("click", closeMenu);
        overlay.addEventListener("click", closeMenu);

        sidebar.querySelectorAll("a").forEach((link) => {
            link.addEventListener("click", closeMenu);
        });

        document.addEventListener("keydown", (event) => {
            if (event.key === "Escape" && body.classList.contains("mobile-nav-open")) {
                closeMenu();
                menuToggle.focus();
            }
        });

        window.addEventListener("resize", () => {
            closeMenu();
        });

        setSidebarAvailable(!mobileMedia.matches);
    }

    function enhanceTable(table) {
        const headers = Array.from(table.querySelectorAll("thead th"))
            .map((header) => header.textContent.trim());

        if (!headers.length) {
            return;
        }

        table.classList.add("responsive-table");
        table.dataset.responsiveReady = "true";

        table.querySelectorAll("tbody tr").forEach((row) => {
            const cells = Array.from(row.children);

            if (cells.length === 1 && Number(cells[0].colSpan) > 1) {
                row.classList.add("responsive-empty-row");
                return;
            }

            cells.forEach((cell, index) => {
                cell.dataset.label = headers[index] || "";
            });
        });
    }

    function enhanceTables(root) {
        if (root instanceof HTMLTableElement) {
            enhanceTable(root);
        }

        const parentTable = root.closest?.("table");
        if (parentTable) {
            enhanceTable(parentTable);
        }

        root.querySelectorAll?.("table").forEach(enhanceTable);
    }

    enhanceTables(document);

    const tableObserver = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            mutation.addedNodes.forEach((node) => {
                if (node instanceof Element) {
                    enhanceTables(node);
                }
            });
        });
    });

    tableObserver.observe(document.body, {
        childList: true,
        subtree: true
    });
});
