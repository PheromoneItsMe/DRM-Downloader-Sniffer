// ==UserScript==
// @name         DRM Automatic Sniffer & Command Logger
// @namespace    http://tampermonkey.net/
// @version      2.7
// @description  Automatically intercepts PSSH, MPD URL, and License URL on any DRM video stream and sends it to local Python DRM-Collector.
// @author       Pheromone
// @match        *://*/*
// @allFrames    true
// @run-at       document-start
// @grant        GM_xmlhttpRequest
// @grant        GM_setValue
// @grant        GM_getValue
// @connect      localhost
// ==/UserScript==

(function () {
    'use strict';

    console.log('[DRM Sniffer v2.7] Active in frame:', window.location.href);

    let lastPssh = '';
    let lastMpdUrl = '';
    let lastLicUrl = '';
    let sendTimeout = null;
    let sentKeys = new Set();

    // Extract exact movie/episode title from main page DOM elements
    function extractPageTitle() {
        let selectors = [
            '.video-title strong',
            '.video-title',
            '.collection-title strong',
            '.collection-title',
            'h1.head strong',
            'h1.head',
            'h1 strong',
            'h1',
            'meta[property="og:title"]',
            'title'
        ];

        for (let sel of selectors) {
            let el = document.querySelector(sel);
            if (el) {
                let text = el.tagName === 'META' ? el.getAttribute('content') : (el.innerText || el.textContent);
                if (text && text.trim() && !text.includes("Vimeo") && !text.includes("VHX") && text.trim() !== "video") {
                    return text.trim();
                }
            }
        }
        return '';
    }

    // Continuously update title on main page and store globally in Tampermonkey storage
    function updateTitleLoop() {
        let title = extractPageTitle();
        if (title) {
            try {
                if (typeof GM_setValue !== 'undefined') {
                    GM_setValue('drm_captured_title', title);
                }
            } catch (e) { }
        }
    }

    if (window.self === window.top) {
        setInterval(updateTitleLoop, 1000);
        window.addEventListener('DOMContentLoaded', updateTitleLoop);
    }

    // Stylish In-Browser Toast Notification (Top Right Corner of Webpage)
    function showBrowserToast(title, message) {
        try {
            let toast = document.getElementById('drm-sniffer-toast');
            if (!toast) {
                toast = document.createElement('div');
                toast.id = 'drm-sniffer-toast';
                toast.style.cssText = `
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    z-index: 9999999;
                    background: linear-gradient(135deg, #10ac84, #1dd1a1);
                    color: #ffffff;
                    padding: 14px 22px;
                    border-radius: 10px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.5);
                    border: 2px solid #10ac84;
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    font-size: 14px;
                    transition: all 0.4s ease;
                    display: flex;
                    flex-direction: column;
                    gap: 4px;
                    pointer-events: none;
                `;
                (document.body || document.documentElement).appendChild(toast);
            }
            toast.innerHTML = `
                <div style="font-weight: bold; font-size: 15px; display: flex; align-items: center; gap: 8px;">
                    🎯 ${title}
                </div>
                <div style="color: #f1f2f6; font-size: 13px;">${message}</div>
            `;
            toast.style.opacity = '1';
            setTimeout(() => {
                if (toast) toast.style.opacity = '0';
            }, 5000);
        } catch (e) {
            console.error('[DRM Sniffer] Toast error:', e);
        }
    }

    function scheduleSend() {
        if (!lastPssh || !lastMpdUrl) return;

        if (sendTimeout) clearTimeout(sendTimeout);

        sendTimeout = setTimeout(() => {
            const dedupeKey = lastPssh + '|' + lastMpdUrl + '|' + lastLicUrl;
            if (sentKeys.has(dedupeKey)) return;
            sentKeys.add(dedupeKey);

            let mainTitle = '';
            try {
                if (typeof GM_getValue !== 'undefined') {
                    mainTitle = GM_getValue('drm_captured_title', '');
                }
            } catch (e) { }

            if (!mainTitle) {
                mainTitle = extractPageTitle();
            }
            if (!mainTitle) {
                mainTitle = document.title || 'video';
            }

            let mainPageUrl = window.location.href;
            try {
                if (window.top && window.top.location) {
                    mainPageUrl = window.top.location.href || mainPageUrl;
                }
            } catch (e) { }

            const payload = {
                pssh: lastPssh,
                mpd_url: lastMpdUrl,
                lic_url: lastLicUrl,
                title: mainTitle,
                page_url: mainPageUrl
            };

            console.log('[DRM Sniffer] Sending DRM Payload with Title:', payload);
            const dataStr = JSON.stringify(payload);

            if (typeof GM_xmlhttpRequest !== 'undefined') {
                GM_xmlhttpRequest({
                    method: 'POST',
                    url: 'http://localhost:8989/catch',
                    headers: { 'Content-Type': 'application/json' },
                    data: dataStr,
                    onload: function (res) {
                        console.log('[DRM Sniffer] Command saved successfully.');
                        showBrowserToast('DRM Видео Перехвачено!', 'Команда сохранена с названием: ' + mainTitle);
                    },
                    onerror: function (err) {
                        console.error('[DRM Sniffer] Collector error:', err);
                    }
                });
            } else {
                fetch('http://localhost:8989/catch', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: dataStr
                }).then(() => {
                    console.log('[DRM Sniffer] Command saved successfully.');
                    showBrowserToast('DRM Видео Перехвачено!', 'Команда сохранена с названием: ' + mainTitle);
                }).catch(err => console.error(err));
            }
        }, 400);
    }

    function checkUrl(url) {
        if (!url || typeof url !== 'string') return;

        if (url.includes('events.gif') || url.includes('segment.') || url.includes('.m4s') || url.includes('.ts') || url.includes('/remux/')) {
            return;
        }

        // Strict MPD manifest check - reject non-signed base URLs
        if (url.includes('.mpd?') || url.endsWith('.mpd') || url.includes('manifest.mpd') || url.includes('/primary/playlist.mpd')) {
            if (url.includes('vimeocdn.com') && !url.includes('exp=') && !url.includes('pathsig=')) {
                return;
            }
            if (lastMpdUrl !== url) {
                console.log('[DRM Sniffer] Intercepted MPD URL:', url);
                lastMpdUrl = url;
                scheduleSend();
            }
        }

        if (url.includes('license/widevine') || url.includes('expressplay.com') || url.includes('lic.drmtoday') || url.includes('widevine?asset_id')) {
            if (lastLicUrl !== url) {
                console.log('[DRM Sniffer] Intercepted License URL:', url);
                lastLicUrl = url;
                scheduleSend();
            }
        }
    }

    function hookEME() {
        if (window.MediaKeySession && window.MediaKeySession.prototype) {
            const origGenerateRequest = window.MediaKeySession.prototype.generateRequest;
            window.MediaKeySession.prototype.generateRequest = function (initDataType, initData) {
                try {
                    if (initData) {
                        const bytes = new Uint8Array(initData);
                        let binary = '';
                        for (let i = 0; i < bytes.byteLength; i++) {
                            binary += String.fromCharCode(bytes[i]);
                        }
                        const b64 = btoa(binary);
                        console.log('[DRM Sniffer] Intercepted PSSH:', b64);
                        lastPssh = b64;
                        scheduleSend();
                    }
                } catch (e) {
                    console.error('[DRM Sniffer] Error parsing initData:', e);
                }
                return origGenerateRequest.apply(this, arguments);
            };
        }
    }

    hookEME();
    window.addEventListener('DOMContentLoaded', hookEME);

    const origFetch = window.fetch;
    window.fetch = async function () {
        const url = arguments[0];
        if (typeof url === 'string') {
            checkUrl(url);
        } else if (url && url.url) {
            checkUrl(url.url);
        }
        return origFetch.apply(this, arguments);
    };

    const origXhrOpen = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function (method, url) {
        checkUrl(url);
        return origXhrOpen.apply(this, arguments);
    };

    function scanPerformanceEntries() {
        try {
            const entries = performance.getEntriesByType('resource');
            for (let i = 0; i < entries.length; i++) {
                checkUrl(entries[i].name);
            }
        } catch (e) { }
    }

    setInterval(scanPerformanceEntries, 1500);

})();
