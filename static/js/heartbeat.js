(() => {
    const HEARTBEAT_URL = "/heartbeat";
    const DEFAULT_WARNING_DELAY_MS = 30 * 60 * 1000;
    const DASHBOARD_DATA_SELECTOR = "#dashboard-data";
    const EXTEND_TRIGGER_SELECTOR = "[data-session-extend]";
    const STATUS_SELECTOR = "[data-session-status]";
    const NOTICE_SELECTOR = ".session-notice";

    const pingHeartbeat = async () => {
        try {
            const response = await fetch(HEARTBEAT_URL, {
                method: "GET",
                cache: "no-store",
                credentials: "same-origin",
                headers: {
                    Accept: "application/json",
                },
            });

            if (!response.ok) {
                return false;
            }

            const payload = await response.json();
            return Boolean(payload.activity_updated);
        } catch (error) {
            return false;
        }
    };

    const setStatusMessage = (element, message, state) => {
        if (!element) {
            return;
        }

        element.textContent = message;
        element.dataset.state = state;
    };

    const initManualHeartbeat = () => {
        const dashboardData = document.querySelector(DASHBOARD_DATA_SELECTOR);
        if (!dashboardData) {
            return;
        }

        const warningDelayMsRaw = Number.parseInt(dashboardData.dataset.sessionWarningDelayMs || "", 10);
        const warningDelayMs = Number.isFinite(warningDelayMsRaw)
            ? Math.max(warningDelayMsRaw, 0)
            : DEFAULT_WARNING_DELAY_MS;

        const notice = document.querySelector(NOTICE_SELECTOR);
        if (notice) {
            window.setTimeout(() => {
                notice.hidden = false;
            }, warningDelayMs);
        }

        const trigger = document.querySelector(EXTEND_TRIGGER_SELECTOR);
        if (!trigger) {
            return;
        }

        const status = document.querySelector(STATUS_SELECTOR);
        trigger.addEventListener("click", async (event) => {
            event.preventDefault();
            if (trigger.hasAttribute("disabled")) {
                return;
            }

            trigger.setAttribute("disabled", "disabled");
            setStatusMessage(status, "Extending session...", "pending");

            const updated = await pingHeartbeat();
            if (updated) {
                setStatusMessage(status, "Session extended.", "success");
            } else {
                setStatusMessage(status, "Could not extend right now. Please try again.", "error");
            }

            trigger.removeAttribute("disabled");
        });
    };

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initManualHeartbeat, { once: true });
    } else {
        initManualHeartbeat();
    }
})();
