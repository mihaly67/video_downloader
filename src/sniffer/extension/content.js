// Injektáljuk az inject.js-t a MAIN világba, hogy hozzáférjen a window objecthez
const s = document.createElement('script');
s.src = chrome.runtime.getURL('inject.js');
s.onload = function() {
    this.remove();
};
(document.head || document.documentElement).appendChild(s);

// Figyeljük a MAIN világból jövő üzeneteket
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
