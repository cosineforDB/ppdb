import pandas as pd
import sqlite3
from pathlib import Path

def import_translation_to_db():
    """將 translation.csv 匯入到 database.db"""

    translation_file = Path("translation.csv")
    db_file = Path("database.db")

    if not translation_file.exists():
        print(f"錯誤：找不到 {translation_file}")
        return

    if not db_file.exists():
        print(f"錯誤：找不到 {db_file}")
        return

    # 讀取 CSV 檔案
    # 使用 utf-8-sig 來處理 BOM
    df = pd.read_csv(translation_file, encoding='utf-8-sig')

    # 清理欄位名稱
    df.columns = df.columns.str.strip()

    # 顯示讀取到的資料
    print(f"讀取到 {len(df)} 筆翻譯資料")
    print(f"欄位：{list(df.columns)}")

    # 移除空白行
    df = df.dropna(subset=['中文名稱', '英文名稱'], how='all')

    # 清理資料
    df['中文名稱'] = df['中文名稱'].str.strip()
    df['英文名稱'] = df['英文名稱'].str.strip().str.upper()

    # 移除完全空白的行
    df = df[df['中文名稱'].notna() & df['英文名稱'].notna()]
    df = df[df['中文名稱'] != '']
    df = df[df['英文名稱'] != '']

    print(f"清理後剩餘 {len(df)} 筆有效資料")

    # 連接資料庫
    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()

    try:
        # 建立翻譯表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Translation (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chinese_name TEXT NOT NULL,
                english_name TEXT NOT NULL,
                UNIQUE(chinese_name, english_name)
            )
        """)

        # 清空舊資料（如果有的話）
        cursor.execute("DELETE FROM Translation")

        # 插入資料
        insert_count = 0
        for _, row in df.iterrows():
            try:
                cursor.execute(
                    "INSERT INTO Translation (chinese_name, english_name) VALUES (?, ?)",
                    (row['中文名稱'], row['英文名稱'])
                )
                insert_count += 1
            except sqlite3.IntegrityError:
                # 跳過重複的資料
                pass

        conn.commit()
        print(f"成功匯入 {insert_count} 筆翻譯資料到 Translation 表")

        # 顯示一些範例資料
        cursor.execute("SELECT * FROM Translation LIMIT 10")
        samples = cursor.fetchall()
        print("\n範例資料：")
        for sample in samples:
            print(f"  {sample[1]} -> {sample[2]}")

        # 建立索引以加速查詢
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chinese_name ON Translation(chinese_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_english_name ON Translation(english_name)")
        conn.commit()
        print("\n已建立索引")

    except Exception as e:
        print(f"錯誤：{e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    import_translation_to_db()
