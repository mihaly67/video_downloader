// Ez az ISOLATED világ, amely képes a chrome.* API-k használatára,
// és kommunikál a MAIN world-ben lévő inject.js-sel.

document.addEventListener('JulesSniffer', (e) => {
    const data = e.detail;
    if (!data) return;

    // A megtalált stream URL-t és adatokat átküldjük a Background workernek
    chrome.runtime.sendMessage({
        action: "FOUND_STREAM",
        payload: {
            type: data.type,
            url: data.url,
            manifestType: data.manifestType,
            pageUrl: window.location.href,
            title: document.title
        }
    });
});
