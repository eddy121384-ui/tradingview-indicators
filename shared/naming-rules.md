# Naming Rules

本文件定義 `tradingview-indicators` repository 的命名規則。目標是讓人類看得懂、AI 搜得到、GitHub / Codex 不容易誤判。

## 核心原則

- 路徑與檔名使用英文小寫。
- 使用連字號 `-` 分隔字詞。
- 避免空格、中文路徑、括號與特殊符號。
- 中文可以放在文件標題與內文，不建議放在檔名。
- 檔名追求可搜尋、可排序、可維護，不追求文學性。

## 標準檔名公式

```text
{project}-{module}-{document-type}-v{version}.{ext}
```

範例：

```text
shiori-map-user-guide-zh-v1.0.md
macro-pressure-map-visual-spec-v0.31.md
wyckoff-regime-radar-mtf-spec-v0.5.md
```

## 資料夾名稱

固定使用英文小寫複數：

```text
specs
docs
prompts
src
assets
archive
```

## 語言代碼

```text
zh  # 繁體中文
en  # English
ja  # 日本語
ko  # 한국어
```

## 日期格式

日期一律使用：

```text
yyyy-mm-dd
```

範例：

```text
2026-06-05
```

## 版本格式

```text
v0.1  草稿
v0.9  接近正式版
v1.0  第一個穩定版
v1.1  小改版
v2.0  大改版
```

## 禁止或避免使用

```text
final
new
copy
latest
真的最後版
final_final
空格
中文路徑
```

## 圖片與素材命名

圖片建議使用頁碼或用途命名：

```text
github-codex-notebook-page-01-v1.0.png
shiori-map-dashboard-screenshot-v1.0.png
```

頁碼請使用 `01`、`02`，避免排序錯亂。

## 文件標題策略

檔名用英文給工具讀，文件標題用中文給人讀。

範例：

檔案路徑：

```text
specs/shiori-map-core-spec-v1.0.md
```

文件標題：

```md
# Shiori Map 核心規格書 v1.0
```
