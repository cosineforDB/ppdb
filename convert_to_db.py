import pandas as pd
import sqlite3
from pathlib import Path

def convert_excel_to_sqlite():
    """將 database.xlsx 轉換為 database.db"""

    # 讀取 Excel 檔案
    excel_file = Path("database.xlsx")
    db_file = Path("database.db")

    # 如果資料庫已存在，先刪除
    if db_file.exists():
        db_file.unlink()

    # 建立 SQLite 連線
    conn = sqlite3.connect(str(db_file))

    try:
        # 讀取 Excel 所有工作表
        xls = pd.ExcelFile(excel_file)
        print(f"找到 {len(xls.sheet_names)} 個工作表:")

        for sheet_name in xls.sheet_names:
            print(f"  處理工作表: {sheet_name}")

            # 讀取工作表資料
            df = pd.read_excel(xls, sheet_name=sheet_name)

            # 清理欄位名稱（移除特殊字元，替換空格為底線）
            df.columns = df.columns.str.strip().str.replace(' ', '_').str.replace('[^\w]', '', regex=True)

            # 將資料寫入 SQLite
            # 將工作表名稱轉換為合法的表格名稱
            table_name = sheet_name.strip().replace(' ', '_').replace('-', '_')
            df.to_sql(table_name, conn, if_exists='replace', index=False)

            print(f"    → 已建立表格 '{table_name}'，共 {len(df)} 筆資料，{len(df.columns)} 個欄位")

        print(f"\n✓ 成功將資料轉換為 {db_file}")

        # 顯示資料庫結構
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()

        print(f"\n資料庫包含 {len(tables)} 個表格:")
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            print(f"  • {table_name}: {count} 筆資料, {len(columns)} 個欄位")

    except Exception as e:
        print(f"錯誤: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    convert_excel_to_sqlite()
