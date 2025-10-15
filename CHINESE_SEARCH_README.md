# 中文搜尋功能 Chinese Search Functionality

## 功能概述 Overview

此專案已成功整合中文搜尋功能，讓使用者可以使用中文農藥名稱來搜尋資料庫中的物質。

This project has successfully integrated Chinese search functionality, allowing users to search for substances in the database using Chinese pesticide names.

## 實作內容 Implementation Details

### 1. 資料庫變更 Database Changes

#### 新增 Translation 表 New Translation Table
```sql
CREATE TABLE Translation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chinese_name TEXT NOT NULL,
    english_name TEXT NOT NULL,
    UNIQUE(chinese_name, english_name)
);

-- 建立索引以加速查詢 Indexes for faster queries
CREATE INDEX idx_chinese_name ON Translation(chinese_name);
CREATE INDEX idx_english_name ON Translation(english_name);
```

#### 資料來源 Data Source
- 檔案：`translation.csv`
- 資料筆數：364 筆中英文對照
- 資料格式：中文名稱,英文名稱

### 2. 新增檔案 New Files

#### `import_translation.py`
用於將 `translation.csv` 的資料匯入到 `database.db` 的 Translation 表中。

Script to import data from `translation.csv` into the Translation table in `database.db`.

執行方式 How to run:
```bash
uv run python import_translation.py
```

#### `test_chinese_search.py`
測試中文搜尋功能的腳本。

Script to test the Chinese search functionality.

執行方式 How to run:
```bash
uv run python test_chinese_search.py
```

### 3. 程式碼更新 Code Updates

#### `main.py` 更新內容

1. **搜尋功能增強** Enhanced Search Function (`PPDBDatabase.search_substances`)
   - 當使用者輸入中文時，系統會先查詢 Translation 表
   - 找到對應的英文名稱後，再搜尋 Identification 表
   - 支援模糊搜尋（LIKE 查詢）

2. **新增輔助方法** New Helper Method (`PPDBDatabase.get_chinese_name`)
   - 根據英文名稱取得對應的中文名稱
   - 用於在詳細頁面顯示中文名稱

3. **使用者介面更新** UI Updates
   - 搜尋框提示文字更新為中英文
   - 物質詳細頁面會顯示中文名稱（如果有的話）

## 使用方式 How to Use

### 1. 匯入翻譯資料 Import Translation Data

首次使用前，需要先匯入翻譯資料：

Before first use, import the translation data:

```bash
uv run python import_translation.py
```

### 2. 啟動應用程式 Start the Application

```bash
uv run python main.py
```

### 3. 進行中文搜尋 Perform Chinese Search

1. 在瀏覽器中開啟 `http://localhost:8080`
2. 點擊 "Search" 或 "搜尋"
3. 在搜尋框中輸入中文農藥名稱，例如：
   - 三亞蟎
   - 賽滅寧
   - 克芬蟎
   - 愛殺松

## 搜尋範例 Search Examples

| 中文名稱 | 英文名稱 | 搜尋結果 |
|---------|---------|---------|
| 三亞蟎 | AMITRAZ | ✓ 成功 |
| 賽滅寧 | CYPERMETHRIN | ✓ 成功 |
| 克芬蟎 | CLOFENTEZINE | ✓ 成功 |
| 愛殺松 | ETHION | ✓ 成功 |

## 技術細節 Technical Details

### 搜尋流程 Search Flow

1. 使用者輸入搜尋關鍵字（中文或英文）
2. 系統檢查 Translation 表，尋找匹配的中文名稱
3. 如果找到：
   - 取得對應的英文名稱
   - 使用英文名稱查詢 Identification 表
4. 如果沒找到：
   - 直接使用輸入的關鍵字查詢 Identification 表（假設為英文）

### 資料庫查詢 Database Queries

#### 中文搜尋 Chinese Search
```sql
-- 步驟 1: 查找翻譯
SELECT english_name FROM Translation
WHERE chinese_name LIKE '%{query}%'

-- 步驟 2: 使用英文名稱搜尋
SELECT DISTINCT i.ID, i.Active, i.CAS_RN, i.Availability_status, i.Canonical_SMILES
FROM Identification i
WHERE UPPER(i.Active) IN (英文名稱列表)
ORDER BY i.Active
LIMIT 100
```

#### 取得中文名稱 Get Chinese Name
```sql
SELECT chinese_name FROM Translation
WHERE UPPER(english_name) = UPPER('{english_name}')
```

## 已知限制 Known Limitations

1. **名稱對應不完全** Incomplete Name Mapping
   - 部分翻譯的英文名稱與資料庫中的實際名稱不完全一致
   - 例如：translation.csv 中的 "FOSETYL-AL" 在資料庫中為 "fosetyl-aluminium"
   - 解決方案：可以更新 translation.csv 或建立別名對應表

2. **模糊搜尋** Fuzzy Search
   - 中文搜尋使用 LIKE 查詢，會返回所有包含該關鍵字的結果
   - 例如：搜尋 "賽" 會返回所有包含 "賽" 字的農藥名稱（25筆）

## 未來改進 Future Improvements

1. 建立更完整的中英文對照表
2. 支援同義詞和別名搜尋
3. 改進名稱匹配算法（例如使用模糊匹配）
4. 在搜尋結果中同時顯示中英文名稱
5. 支援拼音搜尋

## 維護說明 Maintenance Notes

### 更新翻譯資料 Update Translation Data

1. 編輯 `translation.csv` 檔案
2. 重新執行 `import_translation.py`：
   ```bash
   uv run python import_translation.py
   ```

### 備份資料庫 Backup Database

建議定期備份 `database.db` 檔案：
```bash
cp database.db database.db.backup
```

## 測試 Testing

執行測試腳本以驗證搜尋功能：
```bash
uv run python test_chinese_search.py
```

測試涵蓋：
- 單一中文名稱搜尋
- 模糊搜尋（部分關鍵字）
- 多筆結果搜尋
- 無結果搜尋

## 相關檔案 Related Files

- `translation.csv` - 中英文對照表
- `import_translation.py` - 匯入腳本
- `test_chinese_search.py` - 測試腳本
- `main.py` - 主應用程式（已更新）
- `database.db` - SQLite 資料庫（包含 Translation 表）
