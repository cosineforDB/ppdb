"""測試中文搜尋功能"""
import sqlite3

def test_chinese_search():
    """測試中文名稱搜尋功能"""

    db_path = "database.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("=== 測試中文搜尋功能 ===\n")

    # 測試案例
    test_queries = [
        "三亞蟎",
        "賽",
        "克",
        "愛殺松",
        "福賽得"
    ]

    for query in test_queries:
        print(f"搜尋: {query}")
        print("-" * 50)

        # 步驟 1: 從 Translation 表查找英文名稱
        cursor.execute(
            "SELECT chinese_name, english_name FROM Translation WHERE chinese_name LIKE ?",
            (f"%{query}%",)
        )
        translations = cursor.fetchall()

        if translations:
            print(f"找到 {len(translations)} 個翻譯:")
            for cn, en in translations:
                print(f"  {cn} -> {en}")

            # 步驟 2: 使用英文名稱搜尋 Identification 表
            english_names = [t[1] for t in translations]
            placeholders = ','.join('?' * len(english_names))
            sql = f"""
                SELECT ID, Active, CAS_RN, Availability_status
                FROM Identification
                WHERE UPPER(Active) IN ({placeholders})
                LIMIT 10
            """
            cursor.execute(sql, english_names)
            substances = cursor.fetchall()

            print(f"\n找到 {len(substances)} 個物質:")
            for substance in substances:
                print(f"  ID: {substance[0]}, Name: {substance[1]}, CAS: {substance[2]}, Status: {substance[3]}")
        else:
            print("沒有找到翻譯")

        print("\n")

    conn.close()
    print("=== 測試完成 ===")

if __name__ == "__main__":
    test_chinese_search()
