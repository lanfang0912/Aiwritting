# Facebook 私密社團影片下載器

一個用 SwiftUI + WKWebView 製作的 iOS App，讓你在登入臉書後，自動偵測影片並一鍵儲存到照片圖庫。

## 功能

- 內建臉書瀏覽器（保留登入狀態）
- 自動偵測頁面上的影片（含私密社團）
- 下載進度顯示
- 儲存到相簿

## 安裝方式

1. 用 Xcode 開啟 `FacebookVideoDownloader.xcodeproj`
2. 選擇你的 Apple 開發者帳號（免費帳號即可）
3. 接上 iPhone，選為目標裝置
4. 按 ▶ Run

> 免費 Apple 開發者帳號安裝的 App 7 天後需重新安裝。

## 使用方式

1. 開啟 App → 在內建瀏覽器登入臉書
2. 瀏覽到想下載的影片，點播放
3. 畫面下方出現「下載」按鈕 → 點擊
4. 授權相簿權限後，影片自動儲存

## 原理

- `WKWebView` 載入臉書（共用 Safari cookie，保留登入）
- 注入 JavaScript，用 `MutationObserver` 監聽 `<video>` 元素的 `src` 屬性
- 偵測到影片 URL 後透過 `window.webkit.messageHandlers` 傳回 Swift
- 用 `URLSession` 下載，`PHPhotoLibrary` 存入相簿

## 注意事項

- 僅供個人使用
- 請尊重社團成員的隱私與著作權
- 此 App 無法上架 App Store（違反臉書 ToS）
