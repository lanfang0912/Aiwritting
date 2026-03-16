# 創作者覺醒日 AI 超級內容生產線

自動找 3 支 YouTube 外文 CC 字幕影片，透過完整 AI 管線生成可直接人工精修的臉書貼文草稿。

## 自動化流程

- 步驟 1-2：YouTube 搜尋 + 抓 CC 字幕 + Claude 初稿
- 步驟 3：改寫（1200-1500 字、臉書格式）
- 步驟 4：社群寫作教練分析 → 潤飾改寫
- 步驟 5：希塔療癒導師視角 → 融入信念／下載／豐盛顯化
- 步驟 6：加入 YouTube 來源標註
- 輸出：`draft_YYYY-MM-DD_XX.txt`（每支影片一份）

## 搜尋主題

- 伴侶、親子關係訪談
- 心靈成長、療癒
- 豐盛顯化、吸引力法則

## 安裝

```bash
pip install -r requirements.txt
cp .env.example .env
# 編輯 .env，填入 API Keys
