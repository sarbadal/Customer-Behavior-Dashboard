function initRegionFilterDropdown() {
    const dropdown = document.getElementById("region-filter-dropdown");
    const trigger = document.getElementById("region-filter-trigger");
    const menu = document.getElementById("region-filter-menu");

    if (!dropdown || !trigger || !menu) {
        return;
    }

    const countElement = trigger.querySelector(".filter-count");
    const checkboxes = menu.querySelectorAll('input[type="checkbox"][name="region"]');

    const updateCount = () => {
        if (!countElement) {
            return;
        }
        const selectedCount = [...checkboxes].filter((checkbox) => checkbox.checked).length;
        countElement.textContent = selectedCount > 0 ? `${selectedCount} selected` : "All";
    };

    trigger.addEventListener("click", () => {
        const willOpen = !dropdown.classList.contains("open");
        dropdown.classList.toggle("open", willOpen);
        trigger.setAttribute("aria-expanded", String(willOpen));
    });

    document.addEventListener("click", (event) => {
        if (dropdown.contains(event.target)) {
            return;
        }
        dropdown.classList.remove("open");
        trigger.setAttribute("aria-expanded", "false");
    });

    checkboxes.forEach((checkbox) => {
        checkbox.addEventListener("change", updateCount);
    });

    updateCount();
}

function initDateRangeFromQuery() {
    const params = new URLSearchParams(window.location.search);
    const startDateInput = document.getElementById("start-date");
    const endDateInput = document.getElementById("end-date");

    if (startDateInput) {
        const startDate = params.get("start_date");
        if (startDate) {
            startDateInput.value = startDate;
        } else if (!startDateInput.value && startDateInput.min) {
            startDateInput.value = startDateInput.min;
        }
    }

    if (endDateInput) {
        const endDate = params.get("end_date");
        if (endDate) {
            endDateInput.value = endDate;
        } else if (!endDateInput.value && endDateInput.max) {
            endDateInput.value = endDateInput.max;
        }
    }
}

window.DashboardFilters = {
    initRegionFilterDropdown,
    initDateRangeFromQuery
};
