function parseJsonAttr(element, attrName) {
    const raw = element.getAttribute(attrName);
    if (!raw) {
        return [];
    }

    try {
        return JSON.parse(raw);
    } catch (error) {
        console.error(`Failed to parse ${attrName}:`, error);
        return [];
    }
}

window.DashboardUtils = {
    parseJsonAttr
};
