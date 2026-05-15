const LOCAL_PYTHON_SERVER = "http://localhost:8000/api/add_stream";

// Memóriában tároljuk a nemrég talált linkeket, hogy elkerüljük a duplikációt
const recentStreams = new Set();

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === "FOUND_STREAM") {
        const payload = message.payload;
        if (!payload || !payload.url) return;

        // Ne küldjünk minden egyes m3u8 chunk-ot, csak egyedit
        if (recentStreams.has(payload.url)) return;
        recentStreams.add(payload.url);
        setTimeout(() => recentStreams.delete(payload.url), 10000); // 10 mp után elfelejti

        console.log("[Background] Új Stream elkapva:", payload);

        // Cookies kinyerése a Chrome-ból az adott domainhez
        chrome.cookies.getAll({ url: payload.pageUrl }, (cookies) => {
            let cookieStr = "";
            let cookieDict = {};
            cookies.forEach(c => {
                cookieStr += `${c.name}=${c.value}; `;
                cookieDict[c.name] = c.value;
            });

            // Továbbítjuk a lokális Python letöltő Flet Backendnek
            sendToLocalApp({
                ...payload,
                cookies_str: cookieStr,
                cookies_dict: cookieDict
            });
        });
    }
});

function sendToLocalApp(data) {
    fetch(LOCAL_PYTHON_SERVER, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(data)
    }).then(res => {
        console.log("[Background] Sikeresen átadva a lokális Python Core-nak.", res.status);
    }).catch(err => {
        console.log("[Background] Lokális Flet App nem fut, vagy nem elérhető: ", err);
    });
}
