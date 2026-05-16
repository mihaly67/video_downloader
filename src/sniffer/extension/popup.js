document.addEventListener('DOMContentLoaded', () => {
    const sendBtn = document.getElementById('send-btn');

    sendBtn.addEventListener('click', () => {
        chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
            let activeTab = tabs[0];
            if(activeTab && activeTab.url) {
                chrome.runtime.sendMessage({
                    action: "FOUND_STREAM",
                    payload: {
                        type: "PAGE_URL",
                        url: activeTab.url,
                        pageUrl: activeTab.url,
                        title: activeTab.title
                    }
                });
                sendBtn.innerText = "Elküldve a letöltőnek!";
                sendBtn.style.backgroundColor = "#4caf50";
                setTimeout(() => {
                    sendBtn.innerText = "Aktuális oldal küldése letöltésre";
                    sendBtn.style.backgroundColor = "#1976d2";
                }, 2000);
            }
        });
    });
});
