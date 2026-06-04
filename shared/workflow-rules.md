# Workflow Rules

本文件定義 `tradingview-indicators` repository 的 AI 協作流程，適用於 ChatGPT、Codex 與人工 review。

## 核心工作流

```text
討論需求 → 產出規格書 → 寫入 specs → Codex 依規格施工 → Pull Request → Review → Merge
```

## 角色分工

### Eddy

- 定義交易邏輯、使用情境與指標目的。
- 確認規格書是否符合原意。
- Review PR 中的檔案變更。
- 決定是否 merge。

### ChatGPT / Sophira

- 協助整理需求與規格書。
- 協助撰寫 docs、prompts、README。
- 協助檢查 PR 是否越界。
- 不應在未確認情況下改動核心程式邏輯。

### Codex

- 根據 repo 內的 `specs/`、`prompts/` 與 `docs/` 施工。
- 修改指定檔案。
- 產生 diff / PR 供 review。
- 不應自行擴大修改範圍。

## 每次請 Codex 工作前的最低要求

請明確指定：

```text
任務目標：
可以修改的檔案：
不可以修改的檔案：
必須讀取的規格書：
完成後輸出方式：
```

## 建議 Codex 指令模板

```text
請讀取以下檔案：
- indicators/{indicator-name}/specs/{spec-file}.md
- indicators/{indicator-name}/prompts/{prompt-file}.md

任務目標：
請依據上述規格修改 / 新增指定內容。

可以修改：
- indicators/{indicator-name}/docs/...
- indicators/{indicator-name}/src/...

不可以修改：
- shared/
- 其他指標資料夾
- 未指定的核心程式碼

完成後請建立 Pull Request，並在 PR 說明中列出：
1. 修改了哪些檔案
2. 為什麼修改
3. 我應該檢查哪些地方
```

## Review 檢查清單

每次 PR merge 前，至少確認：

- 是否只修改允許範圍內的檔案？
- 是否有動到不該動的指標？
- 是否符合規格書與原本指標定位？
- 是否有更新對應 docs / README？
- 是否有保留舊版或必要備份？

## 分支命名建議

```text
feature/{indicator-name}-{short-task}
fix/{indicator-name}-{short-bug}
docs/{indicator-name}-{short-doc-task}
chore/{repo-level-task}
```

範例：

```text
docs/shiori-map-user-guide
feature/macro-pressure-map-dashboard-colors
fix/wyckoff-regime-radar-mtf-label
chore/initialize-tradingview-indicators
```

## 安全原則

- 正式 repo 不直接改 `main`。
- 文件類任務可以較快，但仍建議走 PR。
- 程式碼任務必須走 PR。
- 大改版前先建立規格書。
- 不要讓 AI 同時改太多無關檔案。
