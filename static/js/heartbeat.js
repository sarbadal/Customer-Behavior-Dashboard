(() => {
    const HEARTBEAT_URL = "/heartbeat";
    const HEARTBEAT_INTERVAL_MS = 60_000;

    let timerId = null;

    const pingHeartbeat = async () => {
        try {
            await fetch(HEARTBEAT_URL, {
                method: "GET",
                cache: "no-store",
                credentials: "same-origin",
                headers: {
                    Accept: "application/json",
                },
            });
        } catch (error) {
            // Keep this silent; heartbeat failures should not disrupt the UI.
        }
    };

    const startHeartbeat = () => {
        void pingHeartbeat();
        timerId = window.setInterval(() => {
            void pingHeartbeat();
        }, HEARTBEAT_INTERVAL_MS);
    };

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", startHeartbeat, { once: true });
    } else {
        startHeartbeat();
    }

    window.addEventListener("beforeunload", () => {
        if (timerId !== null) {
            window.clearInterval(timerId);
        }
    });
})();
