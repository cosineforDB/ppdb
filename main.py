import sqlite3
import pandas as pd
from nicegui import ui
from typing import List, Dict, Any, Optional


class FieldMapper:
    """欄位對應類別，載入中英文對照表"""

    def __init__(self, mapping_file: str = "field_mapping.csv"):
        try:
            self.mapping = pd.read_csv(mapping_file, encoding='utf-8')
            # 建立快速查找字典
            self.field_info = {}
            for _, row in self.mapping.iterrows():
                cell_name = str(row['cell name']).strip() if pd.notna(row['cell name']) else ""
                if cell_name:
                    info = {
                        'en': str(row['Title']) if pd.notna(row['Title']) else cell_name,
                        'zh': str(row['農藥名稱']) if pd.notna(row['農藥名稱']) else "",
                        'class': str(row['類別']) if pd.notna(row['類別']) else "",
                        'sheet': str(row['Sheet']) if pd.notna(row['Sheet']) else "",
                        'column': str(row['Column']) if pd.notna(row['Column']) else "",
                        'cell_name': cell_name
                    }

                    # 生成多種可能的資料庫欄位名稱變體
                    variants = [
                        # 原始名稱
                        cell_name,
                        # 空格轉底線
                        cell_name.replace(' ', '_'),
                        # 空格和破折號轉雙底線
                        cell_name.replace(' - ', '__').replace(' ', '_'),
                        # 移除括號和單位
                        cell_name.replace(' (', '').replace(')', '').replace('/', '').replace(' ', '_'),
                        # 完整轉換（破折號變雙底線，空格變底線）
                        cell_name.replace(' - ', '__').replace('-', '_').replace(' ', '_').replace('(', '').replace(')', '').replace('/', ''),
                    ]

                    # 為每個變體建立映射
                    for variant in variants:
                        if variant:
                            self.field_info[variant] = info
                            # 也嘗試清理連續的底線
                            cleaned = variant.replace('___', '__').replace('__', '_')
                            if cleaned != variant:
                                self.field_info[cleaned] = info

        except Exception as e:
            print(f"Warning: Could not load field mapping: {e}")
            self.field_info = {}

    def get_field_info(self, db_field: str) -> Dict[str, str]:
        """根據資料庫欄位名稱取得欄位資訊"""
        # 嘗試多種匹配方式
        field_variants = [
            db_field,
            db_field.replace('__', '_').replace('___', '_'),
            db_field.replace('_', ' '),
        ]

        for variant in field_variants:
            if variant in self.field_info:
                return self.field_info[variant]

        # 如果找不到，返回預設值
        return {
            'en': db_field.replace('_', ' '),
            'zh': '',
            'class': '',
            'sheet': '',
            'column': '',
            'cell_name': db_field
        }

    def format_label(self, db_field: str, show_chinese: bool = True) -> str:
        """格式化欄位標籤"""
        info = self.get_field_info(db_field)
        if show_chinese and info['zh']:
            return f"{info['en']} / {info['zh']}"
        return info['en']


class PPDBDatabase:
    """PPDB 資料庫存取類別"""

    def __init__(self, db_path: str = "database.db"):
        self.db_path = db_path

    def search_substances(
        self, query: str, search_type: str = "name"
    ) -> List[Dict[str, Any]]:
        """搜尋物質"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            if search_type == "name":
                sql = """
                    SELECT DISTINCT
                        i.ID as id,
                        i.Active as name,
                        i.CAS_RN as cas_rn,
                        i.Availability_status as status,
                        i.Canonical_SMILES as smiles
                    FROM Identification i
                    WHERE i.Active LIKE ?
                    ORDER BY i.Active
                    LIMIT 100
                """
                cursor.execute(sql, (f"%{query}%",))
            elif search_type == "cas":
                sql = """
                    SELECT DISTINCT
                        i.ID as id,
                        i.Active as name,
                        i.CAS_RN as cas_rn,
                        i.Availability_status as status,
                        i.Canonical_SMILES as smiles
                    FROM Identification i
                    WHERE i.CAS_RN LIKE ?
                    ORDER BY i.Active
                    LIMIT 100
                """
                cursor.execute(sql, (f"%{query}%",))
            elif search_type == "smiles":
                sql = """
                    SELECT DISTINCT
                        i.ID as id,
                        i.Active as name,
                        i.CAS_RN as cas_rn,
                        i.Availability_status as status,
                        i.Canonical_SMILES as smiles
                    FROM Identification i
                    WHERE i.Canonical_SMILES LIKE ? OR i.Isomeric_SMILES LIKE ?
                    ORDER BY i.Active
                    LIMIT 100
                """
                cursor.execute(sql, (f"%{query}%", f"%{query}%"))
            elif search_type == "inchi":
                sql = """
                    SELECT DISTINCT
                        i.ID as id,
                        i.Active as name,
                        i.CAS_RN as cas_rn,
                        i.Availability_status as status,
                        i.Canonical_SMILES as smiles
                    FROM Identification i
                    WHERE i.International_Chemical_Identifier_InChI LIKE ?
                    ORDER BY i.Active
                    LIMIT 100
                """
                cursor.execute(sql, (f"%{query}%",))
            elif search_type == "alias":
                sql = """
                    SELECT DISTINCT
                        i.ID as id,
                        i.Active as name,
                        i.CAS_RN as cas_rn,
                        i.Availability_status as status,
                        i.Canonical_SMILES as smiles
                    FROM Identification i
                    LEFT JOIN Aliases a ON i.ID = a.ID
                    WHERE a.Alias LIKE ? OR a.Abbreviation LIKE ?
                    ORDER BY i.Active
                    LIMIT 100
                """
                cursor.execute(sql, (f"%{query}%", f"%{query}%"))

            results = [dict(row) for row in cursor.fetchall()]
            return results
        finally:
            conn.close()

    def get_substance_details(self, substance_id: int) -> Optional[Dict[str, Any]]:
        """取得物質詳細資料"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT * FROM Identification WHERE ID = ?", (substance_id,))
            identification = cursor.fetchone()

            if not identification:
                return None

            cursor.execute("SELECT * FROM Fate WHERE ID = ?", (substance_id,))
            fate = cursor.fetchone()

            cursor.execute("SELECT * FROM Aquatic_Ecotox WHERE ID = ?", (substance_id,))
            aquatic = cursor.fetchone()

            cursor.execute("SELECT * FROM Human WHERE ID = ?", (substance_id,))
            human = cursor.fetchone()

            cursor.execute("SELECT * FROM Aliases WHERE ID = ?", (substance_id,))
            aliases = cursor.fetchall()

            return {
                "identification": dict(identification) if identification else {},
                "fate": dict(fate) if fate else {},
                "aquatic_ecotox": dict(aquatic) if aquatic else {},
                "human": dict(human) if human else {},
                "aliases": [dict(a) for a in aliases],
            }
        finally:
            conn.close()

    def get_all_substances(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """取得所有物質列表"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT
                    ID as id,
                    Active as name,
                    CAS_RN as cas_rn,
                    Availability_status as status
                FROM Identification
                WHERE Active IS NOT NULL AND Active != ''
                ORDER BY Active
                LIMIT ? OFFSET ?
            """,
                (limit, offset),
            )

            results = [dict(row) for row in cursor.fetchall()]
            return results
        finally:
            conn.close()

    def get_total_count(self) -> int:
        """取得總物質數量"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT COUNT(*) as count
                FROM Identification
                WHERE Active IS NOT NULL AND Active != ''
            """
            )
            result = cursor.fetchone()
            return result[0] if result else 0
        finally:
            conn.close()


# 全域變數
db = PPDBDatabase()
field_mapper = FieldMapper()
selected_for_comparison = []


@ui.page("/")
def index():
    """首頁"""
    ui.dark_mode().enable()

    with ui.header().classes("bg-primary text-white"):
        with ui.row().classes("w-full items-center justify-between q-px-md"):
            ui.label("PPDB - Pesticide Properties Database").classes("text-h5 font-bold")
            with ui.row():
                ui.button("Home", on_click=lambda: ui.navigate.to("/")).props("flat").classes("text-white")
                ui.button("Search", on_click=lambda: ui.navigate.to("/search")).props("flat").classes("text-white")
                ui.button("Compare", on_click=lambda: ui.navigate.to("/compare")).props("flat").classes("text-white")

    with ui.column().classes("w-full items-center q-pa-xl"):
        ui.label("Welcome to PPDB").classes("text-h3 q-mb-md")
        ui.label("Pesticide Properties Database - A comprehensive relational database").classes("text-h6 text-grey-6 q-mb-xl")

        with ui.card().classes("w-full max-w-2xl q-pa-lg"):
            ui.label("Quick Start").classes("text-h6 q-mb-md")
            with ui.row().classes("gap-4"):
                ui.button("Search Substances", on_click=lambda: ui.navigate.to("/search"), icon="search").props("size=lg color=primary")
                ui.button("Compare Substances", on_click=lambda: ui.navigate.to("/compare"), icon="compare_arrows").props("size=lg color=secondary")

        with ui.card().classes("w-full max-w-2xl q-pa-lg q-mt-md"):
            ui.label("Database Statistics").classes("text-h6 q-mb-md")
            with ui.grid(columns=3).classes("w-full gap-4"):
                with ui.column().classes("items-center"):
                    ui.label("3,023").classes("text-h4 text-primary")
                    ui.label("Substances").classes("text-grey-6")
                with ui.column().classes("items-center"):
                    ui.label("8").classes("text-h4 text-secondary")
                    ui.label("Data Tables").classes("text-grey-6")
                with ui.column().classes("items-center"):
                    ui.label("100+").classes("text-h4 text-accent")
                    ui.label("Properties").classes("text-grey-6")


@ui.page("/search")
def search_page():
    """搜尋頁面"""
    ui.dark_mode().enable()

    with ui.header().classes("bg-primary text-white"):
        with ui.row().classes("w-full items-center justify-between q-px-md"):
            ui.label("PPDB - Pesticide Properties Database").classes("text-h5 font-bold")
            with ui.row():
                ui.button("Home", on_click=lambda: ui.navigate.to("/")).props("flat").classes("text-white")
                ui.button("Search", on_click=lambda: ui.navigate.to("/search")).props("flat").classes("text-white")
                ui.button("Compare", on_click=lambda: ui.navigate.to("/compare")).props("flat").classes("text-white")

    with ui.column().classes("w-full q-pa-md"):
        ui.label("Search Pesticides").classes("text-h4 q-mb-md")

        # 搜尋輸入區域
        with ui.card().classes("w-full q-pa-md q-mb-md"):
            with ui.row().classes("w-full items-end gap-4"):
                search_input = ui.input(
                    label="Search query",
                    placeholder="Enter substance name, CAS RN, SMILES, InChI, or alias"
                ).classes("flex-grow").props("outlined")

                search_type = ui.select(
                    label="Search by",
                    options={
                        "name": "Substance Name",
                        "cas": "CAS RN",
                        "smiles": "SMILES",
                        "inchi": "InChI",
                        "alias": "Alias",
                    },
                    value="name",
                ).style("min-width: 200px").props("outlined")

                ui.button(
                    "Search",
                    icon="search",
                    on_click=lambda: perform_search(search_input.value, search_type.value, results_container, pagination_container),
                ).props("color=primary")

        # 搜尋結果區域
        results_container = ui.column().classes("w-full")

        # 分頁區域
        pagination_container = ui.column().classes("w-full")

        # 預設顯示第 1 頁
        display_all_substances(results_container, pagination_container, page=1)


def perform_search(query: str, search_type: str, container: ui.column, pagination_container: ui.column):
    """執行搜尋"""
    if not query or query.strip() == "":
        ui.notify("Please enter a search query", type="warning")
        return

    results = db.search_substances(query, search_type)
    display_search_results(results, container)
    # 清除分頁（搜尋結果不分頁，因為已經限制在 100 筆內）
    pagination_container.clear()


def create_pagination(pagination_container: ui.column, current_page: int, total_pages: int, results_container: ui.column):
    """建立分頁元件"""
    pagination_container.clear()

    if total_pages <= 1:
        return

    with pagination_container:
        with ui.card().classes("w-full q-pa-md q-mt-md"):
            with ui.row().classes("w-full items-center justify-center gap-2 flex-wrap"):
                # 上一頁按鈕
                prev_disabled = current_page == 1
                ui.button(
                    "上一頁 / Previous",
                    icon="navigate_before",
                    on_click=lambda: display_all_substances(results_container, pagination_container, page=current_page - 1)
                ).props(f"{'disable' if prev_disabled else ''} outline")

                # 第一頁
                if current_page > 3:
                    ui.button(
                        "1",
                        on_click=lambda: display_all_substances(results_container, pagination_container, page=1)
                    ).props(f"{'unelevated color=primary' if current_page == 1 else 'outline'}")

                    if current_page > 4:
                        ui.label("...").classes("q-px-sm")

                # 當前頁面附近的頁碼
                start_page = max(1, current_page - 2)
                end_page = min(total_pages, current_page + 2)

                for page_num in range(start_page, end_page + 1):
                    ui.button(
                        str(page_num),
                        on_click=lambda p=page_num: display_all_substances(results_container, pagination_container, page=p)
                    ).props(f"{'unelevated color=primary' if page_num == current_page else 'outline'}")

                # 最後一頁
                if current_page < total_pages - 2:
                    if current_page < total_pages - 3:
                        ui.label("...").classes("q-px-sm")

                    ui.button(
                        str(total_pages),
                        on_click=lambda: display_all_substances(results_container, pagination_container, page=total_pages)
                    ).props(f"{'unelevated color=primary' if current_page == total_pages else 'outline'}")

                # 下一頁按鈕
                next_disabled = current_page == total_pages
                ui.button(
                    "下一頁 / Next",
                    icon="navigate_next",
                    on_click=lambda: display_all_substances(results_container, pagination_container, page=current_page + 1)
                ).props(f"{'disable' if next_disabled else ''} outline")

            # 顯示頁碼資訊
            ui.label(f"第 {current_page} 頁 / 共 {total_pages} 頁 | Page {current_page} of {total_pages}").classes("text-center text-grey-6 q-mt-sm")


def display_all_substances(container: ui.column, pagination_container: ui.column, page: int = 1, page_size: int = 50):
    """顯示所有物質（分頁）"""
    container.clear()

    # 計算 offset
    offset = (page - 1) * page_size

    # 取得總數和當前頁資料
    total_count = db.get_total_count()
    total_pages = (total_count + page_size - 1) // page_size
    substances = db.get_all_substances(limit=page_size, offset=offset)

    with container:
        ui.label(f"All Substances | 所有物質 (共 {total_count} 筆，第 {page}/{total_pages} 頁)").classes("text-h6 q-mb-md")

        if not substances:
            ui.label("No substances found").classes("text-grey")
            return

        columns = [
            {"name": "name", "label": "Substance Name", "field": "name", "align": "left", "sortable": True},
            {"name": "cas_rn", "label": "CAS RN", "field": "cas_rn", "align": "left"},
            {"name": "status", "label": "Status", "field": "status", "align": "left"},
            {"name": "actions", "label": "Actions", "field": "actions", "align": "center"},
        ]

        table = ui.table(columns=columns, rows=substances, row_key="id").classes("w-full")
        table.add_slot(
            "body-cell-actions",
            """
            <q-td :props="props">
                <q-btn flat dense color="primary" label="View" @click="$parent.$emit('view', props.row)" />
                <q-btn flat dense color="secondary" label="Add to Compare" @click="$parent.$emit('compare', props.row)" />
            </q-td>
        """,
        )

        table.on("view", lambda e: ui.navigate.to(f"/substance/{e.args['id']}"))
        table.on("compare", lambda e: add_to_comparison(e.args))

    # 建立分頁元件
    create_pagination(pagination_container, page, total_pages, container)


def display_search_results(results: List[Dict], container: ui.column):
    """顯示搜尋結果"""
    container.clear()
    with container:
        ui.label(f"Search Results ({len(results)} found)").classes("text-h6 q-mb-md")

        if not results:
            ui.label("No results found").classes("text-grey")
            ui.button("Show All", on_click=lambda: display_all_substances(container)).classes("q-mt-md")
            return

        columns = [
            {"name": "name", "label": "Substance Name", "field": "name", "align": "left", "sortable": True},
            {"name": "cas_rn", "label": "CAS RN", "field": "cas_rn", "align": "left"},
            {"name": "status", "label": "Status", "field": "status", "align": "left"},
            {"name": "actions", "label": "Actions", "field": "actions", "align": "center"},
        ]

        table = ui.table(columns=columns, rows=results, row_key="id").classes("w-full")
        table.add_slot(
            "body-cell-actions",
            """
            <q-td :props="props">
                <q-btn flat dense color="primary" label="View" @click="$parent.$emit('view', props.row)" />
                <q-btn flat dense color="secondary" label="Add to Compare" @click="$parent.$emit('compare', props.row)" />
            </q-td>
        """,
        )

        table.on("view", lambda e: ui.navigate.to(f"/substance/{e.args['id']}"))
        table.on("compare", lambda e: add_to_comparison(e.args))


def add_to_comparison(substance: Dict[str, Any]):
    """加入比對清單"""
    global selected_for_comparison

    if len(selected_for_comparison) >= 8:
        ui.notify("Maximum 8 substances can be compared", type="warning")
        return

    if any(s["id"] == substance["id"] for s in selected_for_comparison):
        ui.notify("Substance already added to comparison", type="warning")
        return

    selected_for_comparison.append(substance)
    ui.notify(f"Added {substance['name']} to comparison ({len(selected_for_comparison)}/8)", type="positive")


@ui.page("/substance/{substance_id}")
def substance_details(substance_id: int):
    """物質詳細頁面"""
    ui.dark_mode().enable()

    with ui.header().classes("bg-primary text-white"):
        with ui.row().classes("w-full items-center justify-between q-px-md"):
            ui.label("PPDB - Pesticide Properties Database").classes("text-h5 font-bold")
            with ui.row():
                ui.button("Home", on_click=lambda: ui.navigate.to("/")).props("flat").classes("text-white")
                ui.button("Search", on_click=lambda: ui.navigate.to("/search")).props("flat").classes("text-white")
                ui.button("Compare", on_click=lambda: ui.navigate.to("/compare")).props("flat").classes("text-white")

    details = db.get_substance_details(substance_id)

    if not details:
        with ui.column().classes("w-full items-center q-pa-xl"):
            ui.label("Substance not found").classes("text-h4 text-negative")
            ui.button("Back to Search", on_click=lambda: ui.navigate.to("/search")).classes("q-mt-md")
        return

    info = details["identification"]

    with ui.column().classes("w-full q-pa-md"):
        # 標題
        with ui.row().classes("w-full items-center q-mb-md"):
            ui.button(icon="arrow_back", on_click=lambda: ui.navigate.to("/search")).props("flat round")
            ui.label(info.get("Active", "N/A")).classes("text-h4 q-ml-md")

        # 基本資訊
        with ui.card().classes("w-full q-pa-md q-mb-md"):
            ui.label("General Information / 一般資料").classes("text-h6 q-mb-md")
            with ui.grid(columns=2).classes("w-full gap-4"):
                display_field("CAS_RN", info.get("CAS_RN"))
                display_field("Availability_status", info.get("Availability_status"))
                display_field("Canonical_SMILES", info.get("Canonical_SMILES"))
                display_field("International_Chemical_Identifier_InChI", info.get("International_Chemical_Identifier_InChI"))
                display_field("Molecular_mass", info.get("Molecular_mass"))

        # 別名
        if details["aliases"]:
            with ui.card().classes("w-full q-pa-md q-mb-md"):
                ui.label("Aliases").classes("text-h6 q-mb-md")
                for alias in details["aliases"]:
                    if alias.get("Alias"):
                        ui.label(f"• {alias['Alias']}")

        # Environmental Fate
        if details["fate"]:
            with ui.card().classes("w-full q-pa-md q-mb-md"):
                ui.label("Environmental Fate / 環境命運").classes("text-h6 q-mb-md")
                fate = details["fate"]
                with ui.grid(columns=2).classes("w-full gap-4"):
                    display_field("Solubility__In_water_at_20_degC_mgl", fate.get("Solubility__In_water_at_20_degC_mgl"))
                    display_field("LogP", fate.get("LogP"))
                    display_field("Vapour_pressure_at_20_degC_mPa", fate.get("Vapour_pressure_at_20_degC_mPa"))
                    display_field("Henrys_law_constant_at_25_degC_Pam3mol", fate.get("Henrys_law_constant_at_25_degC_Pam3mol"))

        # Aquatic Ecotoxicology
        if details["aquatic_ecotox"]:
            with ui.card().classes("w-full q-pa-md q-mb-md"):
                ui.label("Aquatic Ecotoxicology / 水生生態毒理").classes("text-h6 q-mb-md")
                eco = details["aquatic_ecotox"]
                with ui.grid(columns=2).classes("w-full gap-4"):
                    display_field("Fish__Acute_96hr_LC50_mgl__TEMPERATE", eco.get("Fish__Acute_96hr_LC50_mgl__TEMPERATE"))
                    display_field("Algae__Acute_72hr_EC50_growth_mgl", eco.get("Algae__Acute_72hr_EC50_growth_mgl"))

        # Human Health
        if details["human"]:
            with ui.card().classes("w-full q-pa-md q-mb-md"):
                ui.label("Human Health / 人體健康").classes("text-h6 q-mb-md")
                human = details["human"]
                with ui.grid(columns=2).classes("w-full gap-4"):
                    display_field("Mammals__Dermal_LD50_mgkg", human.get("Mammals__Dermal_LD50_mgkg"))
                    display_field("Mammals__Inhalation_LC50_mgl", human.get("Mammals__Inhalation_LC50_mgl"))
                    display_field("Acceptable_Daily_Intake_ADI_mgkg_bw", human.get("Acceptable_Daily_Intake_ADI_mgkg_bw"))
                    display_field("Acute_Reference_Dose_ARfD_mgkg_BWday", human.get("Acute_Reference_Dose_ARfD_mgkg_BWday"))


def display_field(db_field: str, value: Any, show_metadata: bool = True):
    """顯示欄位（包含中文和資料來源資訊）"""
    global field_mapper
    info = field_mapper.get_field_info(db_field)

    with ui.column().classes("q-mb-md"):
        # 顯示欄位標籤（中英文）
        if info['zh']:
            ui.label(f"{info['en']} / {info['zh']}").classes("text-body1 font-bold")
        else:
            ui.label(info['en']).classes("text-body1 font-bold")

        # 顯示值
        display_value = str(value) if value not in [None, "", "nan"] else "N/A"
        ui.label(display_value).classes("text-h6 q-ml-md")

        # 顯示資料來源資訊（Sheet, Column）
        if show_metadata and info['sheet'] and info['column']:
            with ui.row().classes("q-mt-xs items-center gap-1"):
                ui.icon("info", size="xs").classes("text-grey-6")
                ui.label(f"來源: {info['sheet']} 表，欄位 {info['column']}").classes("text-caption text-grey-6")


@ui.page("/compare")
def compare_page():
    """比對頁面"""
    ui.dark_mode().enable()

    with ui.header().classes("bg-primary text-white"):
        with ui.row().classes("w-full items-center justify-between q-px-md"):
            ui.label("PPDB - Pesticide Properties Database").classes("text-h5 font-bold")
            with ui.row():
                ui.button("Home", on_click=lambda: ui.navigate.to("/")).props("flat").classes("text-white")
                ui.button("Search", on_click=lambda: ui.navigate.to("/search")).props("flat").classes("text-white")
                ui.button("Compare", on_click=lambda: ui.navigate.to("/compare")).props("flat").classes("text-white")

    with ui.column().classes("w-full q-pa-md"):
        ui.label("Compare Substances").classes("text-h4 q-mb-md")

        global selected_for_comparison

        if not selected_for_comparison:
            with ui.card().classes("w-full q-pa-lg text-center"):
                ui.label("No substances selected for comparison").classes("text-h6 text-grey")
                ui.label("Search for substances and click 'Add to Compare' to add them here").classes("text-grey q-mt-md")
                ui.button("Go to Search", on_click=lambda: ui.navigate.to("/search"), icon="search").classes("q-mt-lg").props("color=primary size=lg")
            return

        # 顯示已選擇的物質
        with ui.card().classes("w-full q-pa-md q-mb-md"):
            ui.label(f"Selected Substances ({len(selected_for_comparison)}/8)").classes("text-h6 q-mb-md")
            with ui.row().classes("w-full gap-2 flex-wrap"):
                for i, substance in enumerate(selected_for_comparison):
                    with ui.chip(text=substance["name"], removable=True).props("color=primary"):
                        pass
                    # Note: Chip removal needs to be handled differently in this structure

            ui.button("Clear All", on_click=lambda: clear_comparison(), icon="clear").props("flat color=negative")

        # 比對表格
        if len(selected_for_comparison) >= 2:
            display_comparison_table()
        else:
            ui.label("Select at least 2 substances to compare").classes("text-grey q-mt-md")


def clear_comparison():
    """清除比對清單"""
    global selected_for_comparison
    selected_for_comparison = []
    ui.navigate.to("/compare")


def display_comparison_table():
    """顯示比對表格"""
    global selected_for_comparison, field_mapper

    with ui.card().classes("w-full q-pa-md"):
        ui.label("Comparison Table / 比對表格").classes("text-h6 q-mb-md")

        # 取得詳細資料
        details_list = []
        for substance in selected_for_comparison:
            details = db.get_substance_details(substance["id"])
            if details:
                details_list.append(details)

        if not details_list:
            ui.label("Error loading substance details").classes("text-negative")
            return

        # 定義要比對的欄位（使用資料庫欄位名稱）
        # 格式：(資料庫欄位名, 取值函數, 分類)
        comparison_fields = [
            # 基本資訊
            ("Active", lambda d: d["identification"].get("Active"), "一般資料"),
            ("CAS_RN", lambda d: d["identification"].get("CAS_RN"), "一般資料"),
            ("Availability_status", lambda d: d["identification"].get("Availability_status"), "一般資料"),
            ("Molecular_mass", lambda d: d["identification"].get("Molecular_mass"), "一般資料"),
            ("Canonical_SMILES", lambda d: d["identification"].get("Canonical_SMILES"), "一般資料"),
            ("International_Chemical_Identifier_InChI", lambda d: d["identification"].get("International_Chemical_Identifier_InChI"), "一般資料"),

            # 環境命運
            ("Solubility__In_water_at_20_degC_mgl", lambda d: d["fate"].get("Solubility__In_water_at_20_degC_mgl"), "環境命運"),
            ("LogP", lambda d: d["fate"].get("LogP"), "環境命運"),
            ("Vapour_pressure_at_20_degC_mPa", lambda d: d["fate"].get("Vapour_pressure_at_20_degC_mPa"), "環境命運"),
            ("Henrys_law_constant_at_25_degC_Pam3mol", lambda d: d["fate"].get("Henrys_law_constant_at_25_degC_Pam3mol"), "環境命運"),
            ("Melting_point_degC", lambda d: d["fate"].get("Melting_point_degC"), "環境命運"),
            ("Boiling_point_deg_C_1atm", lambda d: d["fate"].get("Boiling_point_deg_C_1atm"), "環境命運"),

            # 水生生態毒理
            ("Fish__Acute_96hr_LC50_mgl__TEMPERATE", lambda d: d["aquatic_ecotox"].get("Fish__Acute_96hr_LC50_mgl__TEMPERATE"), "生態毒理"),
            ("Algae__Acute_72hr_EC50_growth_mgl", lambda d: d["aquatic_ecotox"].get("Algae__Acute_72hr_EC50_growth_mgl"), "生態毒理"),

            # 人體健康
            ("Mammals__Dermal_LD50_mgkg", lambda d: d["human"].get("Mammals__Dermal_LD50_mgkg"), "人體健康"),
            ("Mammals__Inhalation_LC50_mgl", lambda d: d["human"].get("Mammals__Inhalation_LC50_mgl"), "人體健康"),
            ("Acceptable_Daily_Intake_ADI_mgkg_bw", lambda d: d["human"].get("Acceptable_Daily_Intake_ADI_mgkg_bw"), "人體健康"),
            ("Acute_Reference_Dose_ARfD_mgkg_BWday", lambda d: d["human"].get("Acute_Reference_Dose_ARfD_mgkg_BWday"), "人體健康"),
        ]

        # 按類別分組顯示
        current_category = None

        for db_field, value_getter, category in comparison_fields:
            # 如果是新類別，顯示類別標題
            if category != current_category:
                current_category = category
                ui.separator().classes("q-my-md")
                ui.label(category).classes("text-h6 text-primary q-mb-sm")

            # 取得欄位資訊
            field_info = field_mapper.get_field_info(db_field)

            # 建立該欄位的比對行
            with ui.row().classes("w-full q-mb-md items-start"):
                # 左側：欄位名稱（固定寬度）
                with ui.column().classes("q-mr-md").style("min-width: 250px; max-width: 250px"):
                    # 顯示中英文名稱
                    if field_info['zh']:
                        ui.label(f"{field_info['en']}").classes("text-body2 font-bold")
                        ui.label(f"{field_info['zh']}").classes("text-caption text-grey-7")
                    else:
                        ui.label(field_info['en']).classes("text-body2 font-bold")

                    # 顯示資料來源
                    if field_info['sheet'] and field_info['column']:
                        with ui.row().classes("items-center gap-1 q-mt-xs"):
                            ui.icon("info", size="xs").classes("text-grey-6")
                            ui.label(f"{field_info['sheet']}:{field_info['column']}").classes("text-caption text-grey-6")

                # 右側：各物質的值（橫向排列）
                with ui.row().classes("flex-grow gap-4 flex-wrap"):
                    for i, details in enumerate(details_list):
                        value = value_getter(details)
                        display_value = str(value) if value not in [None, "", "nan"] else "N/A"

                        with ui.card().classes("q-pa-sm").style("min-width: 150px"):
                            ui.label(details["identification"].get("Active", f"#{i+1}")).classes("text-caption text-grey-7")
                            ui.label(display_value).classes("text-body1")


def main():
    """主程式進入點"""
    ui.run(title="PPDB - Pesticide Properties Database", port=8080, reload=False, show=False)


if __name__ == "__main__":
    main()
