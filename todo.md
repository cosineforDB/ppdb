- [x] 網頁上所顯示的資料，目前有10個出處，但還有其他的出處來源沒有顯示，分別是 Identification 裡的 [BH BK BJ BL AT AW BB], Fate 裡的 [N P Z AE AQ AS AU BP BW CA AN], Terrestrial Ecotox 裡的 [D N BH X], Human 裡的 [Y AA AJ AK AL AM AN AO AP AQ AR AS AT AU AV], 以上所列的出處來源必須呈現在網頁上

- [x] 其中 Terrestrial Ecotox, Aquatic Ecotox 的呈現方式略有不同，他們要呈現的格式是 {大於;等於} {數值} {單位}，例如 Terrestrial Ecotox 為 D , 則要顯示的值為  database.xlsx 裡的 Terrestrial Ecobox sheetname 裡的 E {大小} D {數值} F {單位}，另一個例子是Aquatic Ecotox 的 AI ，則要顯示的值為 database.xlsx 裡的 Aquatic Ecotox sheetname 裡的 AJ {大於; 等於} AI {數值} AK {單位}

## 已完成修改摘要 (2025-10-14)

### 新增欄位顯示：

1. **Identification 區段** - 新增 7 個欄位：
   - BH: Isomerism (異構性)
   - BK: Chemical formula (化學式)
   - BJ: Isomeric SMILES (異構 SMILES)
   - BL: International Chemical Identifier key (InChIKey) (國際化學識別碼)
   - AT: Pesticide type (農藥類型)
   - AW: Substance group (物質類別)
   - BB: Mode of action (作用機制)

2. **Fate 區段** - 新增 11 個欄位：
   - N: Melting point (熔點)
   - P: Boiling point (沸點)
   - Z: Dissociation constant (pKa) (解離常數)
   - AE: Henry's law constant (亨利定律常數)
   - AQ: Soil DT50 - Typical (土壤降解半衰期 - 典型)
   - AS: Soil DT50 - Lab (土壤降解半衰期 - 實驗室)
   - AU: Soil DT50 - Field (土壤降解半衰期 - 田間)
   - BP: Water-sediment DT50 (水-沉積物系統半衰期)
   - BW: Koc (線性土壤吸附係數)
   - CA: Kfoc (Freundlich 吸附係數)
   - AN: Bioconcentration factor (生物濃縮係數)

3. **Terrestrial Ecotox 區段** - 新增整個區段，包含 4 個欄位：
   - D: Mammals - Acute oral LD50 (哺乳類急性口服 LD50)
   - N: Birds - Acute LD50 (鳥類急性 LD50)
   - BH: Earthworms - Acute 14d LC50 (蚯蚓急性 14 日 LC50)
   - X: Honeybees - Contact acute 48hr LD50 (蜜蜂接觸急性 LD50)

4. **Human 區段** - 新增 15 個欄位：
   - Y: AOEL - Acceptable Operator Exposure Level (可接受作業者暴露量)
   - AA: Percutaneous penetration studies (皮膚滲透率研究)
   - AJ: Carcinogen (致癌物)
   - AK: Genotoxic (基因毒性)
   - AL: Endocrine distrupter (內分泌干擾物)
   - AM: Reproduction/development effects (生殖/發育影響)
   - AN: Acetyl cholinesterase inhibitor (乙醯膽鹼酯酶抑制劑)
   - AO: Neurotoxicant (神經毒性)
   - AP: Respiratory tract irritant (呼吸道刺激物)
   - AQ: Skin irritant (皮膚刺激物)
   - AR: Skin sensitiser (皮膚致敏物)
   - AS: Eye irritant (眼刺激物)
   - AT: Phototoxicant (光毒性)
   - AU: General human health issues (一般人類健康問題)
   - AV: Handling issues (處理問題)

### 特殊格式化處理：

實現了 Terrestrial Ecotox 和 Aquatic Ecotox 欄位的特殊顯示格式：
- 格式：{比較運算符} {數值} {單位}
- 例如："= 150.0 mg/kg BW/day"
- 比較運算符從資料庫的 `<>` 前綴欄位中讀取（如 `__Mammals__Acute_oral_LD50`）

### 技術修改：

1. 更新 `get_substance_details()` 函數以包含 Terrestrial_Ecotox 資料
2. 新增 `format_ecotox_value()` 輔助函數來格式化帶比較運算符的值
3. 更新 `display_field()` 函數以支援 Ecotox 欄位的特殊格式化
4. 在物質詳細頁面中新增所有缺少的欄位顯示
5. **更新比對表格 (`display_comparison_table()`)** 以包含所有新增欄位
   - 新增所有 Identification、Fate、Human 的缺少欄位
   - 加入完整的 Terrestrial Ecotox 區段
   - Ecotox 欄位在比對表格中也使用特殊格式化（顯示比較運算符）

### 比對表格更新 (2025-10-14)：

比對表格現在包含與詳細頁面相同的所有欄位：
- **一般資料 (Identification)**: 13 個欄位（包含新增的 7 個）
- **環境命運 (Fate)**: 14 個欄位（包含新增的 11 個）
- **陸生生態毒理 (Terrestrial Ecotox)**: 4 個欄位（新區段）
- **水生生態毒理 (Aquatic Ecotox)**: 2 個欄位
- **人體健康 (Human)**: 19 個欄位（包含新增的 15 個）

**總計：52 個比對欄位**

Ecotox 欄位在比對表格中的顯示格式：
- 使用 `format_ecotox_value()` 函數
- 自動顯示比較運算符（如 `= 150.0 mg/kg BW/day`）
- 與詳細頁面的顯示格式完全一致