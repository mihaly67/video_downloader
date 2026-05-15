(async () => {
    // Ebbe a JS-be injectáljuk a fetch és XMLHttpRequest proxy-t a MAIN (valós oldal) világában,
    // hogy le tudjuk hallgatni a dinamikusan betöltődő streameket.

    const proxy = (object, method, handler) => {
        const original = object[method];
        if (typeof original !== "function") return;

        Object.defineProperty(object, method, {
            value: new Proxy(original, { apply: handler }),
            configurable: true,
            writable: true
        });
    };

    const getManifestType = (text) => {
        const lower = typeof text === 'string' ? text.toLowerCase() : '';
        if (lower.includes('<mpd') && lower.includes('</mpd>')) {
            return "DASH";
        } else if (lower.includes('#extm3u')) {
            return "HLS";
        }
        return null;
    };

    function notifyExtension(type, url, extraData = {}) {
        // Átküldünk egy CustomEvent-et az ISOLATED világ content_script.js-ének
        const evt = new CustomEvent('JulesSniffer', {
            detail: { type: type, url: url, ...extraData }
        });
        document.dispatchEvent(evt);
    }

    // --- XMLHttpRequest hívások elfogása ---
    proxy(XMLHttpRequest.prototype, "open", (target, thisArg, args) => {
        const [method, url] = args;
        thisArg.requestMethod = method ? method.toUpperCase() : "GET";
        thisArg.requestURL = url;

        // Direkteben vizsgáljuk, hátha a URL maga egy stream
        if (typeof url === 'string' && (url.includes('.m3u8') || url.includes('.mpd'))) {
            notifyExtension('STREAM_URL_FOUND', url);
        }
        return target.apply(thisArg, args);
    });

    proxy(XMLHttpRequest.prototype, "send", (target, thisArg, args) => {
        thisArg.addEventListener("readystatechange", async () => {
            if (thisArg.readyState !== 4) return;

            let body = null;
            if (thisArg.responseType === "" || thisArg.responseType === "text") {
                body = thisArg.responseText;
            }
            if (body) {
                const manifest_type = getManifestType(body);
                if (manifest_type) {
                    console.log("[JulesSniffer] XHR Manifest megtalálva:", thisArg.responseURL);
                    notifyExtension('MANIFEST_BODY_FOUND', thisArg.responseURL, { manifestType: manifest_type });
                }
            }
        });
        return target.apply(thisArg, args);
    });

    // --- window.fetch hívások elfogása ---
    proxy(window, "fetch", async (target, thisArg, args) => {
        const url = typeof args[0] === "string" ? args[0] : args[0]?.url;
        if (typeof url === 'string' && (url.includes('.m3u8') || url.includes('.mpd'))) {
            notifyExtension('STREAM_URL_FOUND', url);
        }

        const response = await target.apply(thisArg, args);
        try {
            if (response && response.ok) {
                const clonedResponse = response.clone();
                // Check if it's text/html or xml or generic text before converting to text to avoid large binary blobs
                const contentType = clonedResponse.headers.get("content-type") || "";
                if (contentType.includes("text/") || contentType.includes("application/json") || contentType.includes("xml") || url.includes('.m3u8')) {
                    const text = await clonedResponse.text();
                    const manifest_type = getManifestType(text);
                    if (manifest_type) {
                        console.log("[JulesSniffer] Fetch Manifest megtalálva:", url);
                        notifyExtension('MANIFEST_BODY_FOUND', url, { manifestType: manifest_type });
                    }
                }
            }
        } catch (err) {
            // Ignoráljuk a fetch klónozási hibákat
        }
        return response;
    });

})();
