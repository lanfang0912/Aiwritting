import Foundation
import Photos
import SwiftUI

@MainActor
class VideoDownloader: ObservableObject {
    @Published var videoURLs: [String] = []
    @Published var statusMessage: String = ""
    @Published var showBanner: Bool = false
    @Published var isDownloading: Bool = false
    @Published var progress: Double = 0
    @Published var showPermissionAlert: Bool = false

    var statusIcon: String {
        if isDownloading { return "arrow.down.circle" }
        if videoURLs.isEmpty { return "play.circle" }
        return "arrow.down.circle.fill"
    }

    var statusColor: Color {
        isDownloading ? .blue : (videoURLs.isEmpty ? .gray : .green)
    }

    func updateVideoURLs(_ urls: [String]) {
        let unique = Array(Set(urls))
        guard !unique.isEmpty else { return }
        videoURLs = unique
        statusMessage = "偵測到 \(unique.count) 個影片，點「下載」儲存到相簿"
        showBanner = true
    }

    func resetDetection() {
        guard !isDownloading else { return }
        videoURLs = []
        showBanner = false
    }

    func downloadVideo() {
        guard let urlString = videoURLs.first,
              let url = URL(string: urlString) else { return }

        Task {
            await requestPhotoPermission { granted in
                if granted {
                    Task { await self.performDownload(from: url) }
                } else {
                    self.showPermissionAlert = true
                }
            }
        }
    }

    private func performDownload(from url: URL) async {
        isDownloading = true
        progress = 0
        statusMessage = "下載中..."

        do {
            let (localURL, _) = try await URLSession.shared.download(from: url) { bytesWritten, totalBytesWritten, totalExpected in
                if totalExpected > 0 {
                    DispatchQueue.main.async {
                        self.progress = Double(totalBytesWritten) / Double(totalExpected)
                    }
                }
            }

            // 把暫存檔案移到有 .mp4 副檔名的位置（PHPhotoLibrary 需要）
            let dest = localURL.deletingLastPathComponent().appendingPathComponent("fb_video.mp4")
            try? FileManager.default.removeItem(at: dest)
            try FileManager.default.moveItem(at: localURL, to: dest)

            try await PHPhotoLibrary.shared().performChanges {
                PHAssetChangeRequest.creationRequestForAssetFromVideo(atFileURL: dest)
            }

            statusMessage = "已儲存到相簿！"
            statusIcon(success: true)
        } catch {
            statusMessage = "下載失敗：\(error.localizedDescription)"
        }

        isDownloading = false
        progress = 0

        // 3 秒後自動隱藏 banner
        try? await Task.sleep(nanoseconds: 3_000_000_000)
        showBanner = false
        videoURLs = []
    }

    private func statusIcon(success: Bool) {}

    private func requestPhotoPermission(completion: @escaping (Bool) -> Void) async {
        let status = PHPhotoLibrary.authorizationStatus(for: .addOnly)
        switch status {
        case .authorized, .limited:
            completion(true)
        case .notDetermined:
            let result = await PHPhotoLibrary.requestAuthorization(for: .addOnly)
            completion(result == .authorized || result == .limited)
        default:
            completion(false)
        }
    }
}

// URLSession download with progress
extension URLSession {
    func download(from url: URL, progress: @escaping (Int64, Int64, Int64) -> Void) async throws -> (URL, URLResponse) {
        try await withCheckedThrowingContinuation { continuation in
            let task = self.downloadTask(with: url) { localURL, response, error in
                if let error = error {
                    continuation.resume(throwing: error)
                } else if let localURL, let response {
                    continuation.resume(returning: (localURL, response))
                }
            }
            let observation = task.progress.observe(\.fractionCompleted) { p, _ in
                progress(p.completedUnitCount, p.completedUnitCount, p.totalUnitCount)
            }
            task.resume()
            // observation 持有到 task 完成
            _ = observation
        }
    }
}
