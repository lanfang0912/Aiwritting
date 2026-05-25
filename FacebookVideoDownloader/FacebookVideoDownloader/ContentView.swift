import SwiftUI
import WebKit
import Photos

struct ContentView: View {
    @StateObject private var downloader = VideoDownloader()

    var body: some View {
        ZStack(alignment: .bottom) {
            FacebookWebView(downloader: downloader)
                .ignoresSafeArea()

            if downloader.showBanner {
                BannerView(downloader: downloader)
                    .transition(.move(edge: .bottom).combined(with: .opacity))
                    .animation(.spring(), value: downloader.showBanner)
            }
        }
        .alert("需要相簿權限", isPresented: $downloader.showPermissionAlert) {
            Button("前往設定") {
                UIApplication.shared.open(URL(string: UIApplication.openSettingsURLString)!)
            }
            Button("取消", role: .cancel) {}
        } message: {
            Text("請在設定中允許此 App 存取你的照片圖庫。")
        }
    }
}

// MARK: - Banner UI

struct BannerView: View {
    @ObservedObject var downloader: VideoDownloader

    var body: some View {
        VStack(spacing: 8) {
            HStack {
                Image(systemName: downloader.statusIcon)
                    .foregroundColor(downloader.statusColor)
                Text(downloader.statusMessage)
                    .font(.subheadline)
                    .foregroundColor(.primary)
                Spacer()
                if downloader.isDownloading {
                    ProgressView()
                        .scaleEffect(0.8)
                } else if downloader.videoURLs.count > 0 {
                    Button("下載") {
                        downloader.downloadVideo()
                    }
                    .buttonStyle(.borderedProminent)
                    .controlSize(.small)
                }
            }

            if downloader.isDownloading {
                ProgressView(value: downloader.progress)
                    .progressViewStyle(.linear)
            }
        }
        .padding()
        .background(.ultraThinMaterial)
        .cornerRadius(16)
        .shadow(radius: 8)
        .padding()
    }
}
