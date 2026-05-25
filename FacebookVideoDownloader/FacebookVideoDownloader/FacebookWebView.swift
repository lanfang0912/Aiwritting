import SwiftUI
import WebKit

struct FacebookWebView: UIViewRepresentable {
    @ObservedObject var downloader: VideoDownloader

    func makeCoordinator() -> Coordinator {
        Coordinator(downloader: downloader)
    }

    func makeUIView(context: Context) -> WKWebView {
        let config = WKWebViewConfiguration()
        config.allowsInlineMediaPlayback = true
        config.mediaTypesRequiringUserActionForPlayback = []

        // 注入 JS：監聽頁面上所有 video 元素
        let script = WKUserScript(
            source: videoDetectionJS,
            injectionTime: .atDocumentEnd,
            forMainFrameOnly: false
        )
        config.userContentController.addUserScript(script)
        config.userContentController.add(context.coordinator, name: "videoDetected")

        let webView = WKWebView(frame: .zero, configuration: config)
        webView.navigationDelegate = context.coordinator

        // 用 iPhone User Agent，讓臉書顯示手機版
        webView.customUserAgent = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"

        let url = URL(string: "https://www.facebook.com")!
        webView.load(URLRequest(url: url))

        context.coordinator.webView = webView
        return webView
    }

    func updateUIView(_ uiView: WKWebView, context: Context) {}

    // MARK: - JavaScript 注入

    private var videoDetectionJS: String {
        """
        (function() {
            function reportVideos() {
                const videos = document.querySelectorAll('video');
                const urls = [];
                videos.forEach(v => {
                    if (v.src && v.src.startsWith('http')) urls.push(v.src);
                    v.querySelectorAll('source').forEach(s => {
                        if (s.src && s.src.startsWith('http')) urls.push(s.src);
                    });
                });
                if (urls.length > 0) {
                    window.webkit.messageHandlers.videoDetected.postMessage(urls);
                }
            }

            // 監聽 video 元素播放事件
            document.addEventListener('play', function(e) {
                if (e.target.tagName === 'VIDEO') {
                    setTimeout(reportVideos, 500);
                }
            }, true);

            // 用 MutationObserver 監聽動態載入的 video
            const observer = new MutationObserver(() => {
                const videos = document.querySelectorAll('video[src]');
                if (videos.length > 0) reportVideos();
            });
            observer.observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ['src'] });
        })();
        """
    }

    // MARK: - Coordinator

    class Coordinator: NSObject, WKNavigationDelegate, WKScriptMessageHandler {
        let downloader: VideoDownloader
        weak var webView: WKWebView?

        init(downloader: VideoDownloader) {
            self.downloader = downloader
        }

        // 每次頁面導航完成後重新注入 JS（處理 SPA 換頁）
        func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
            downloader.resetDetection()
        }

        // 接收 JS 傳回的影片 URL
        func userContentController(_ controller: WKUserContentController, didReceive message: WKScriptMessage) {
            guard message.name == "videoDetected",
                  let urls = message.body as? [String] else { return }
            DispatchQueue.main.async {
                self.downloader.updateVideoURLs(urls)
            }
        }
    }
}
