#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
final.py
後端友善版本（仍用 Gradio 當展示/測試入口）

改動重點：
1) 篩選回傳 JSON（dict），前端好串
2) 產品資料不在 import 當下綁死，可重載
3) 讀取 data/merged_products_with_series.json（相對專案根）
"""

import os
import json
import gradio as gr
from typing import Any, Dict, List

# =========================
# 路徑設定（建議專案根目錄）
# =========================
# 讓資料檔路徑相對於「專案根」而非這支檔案的位置：
# - 若 final.py 放在 backend/，ROOT_DIR 會是上一層
# - 若 final.py 放在根目錄，ROOT_DIR 就是當層
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(THIS_DIR, "..")) if os.path.basename(THIS_DIR).lower() in ("backend", "server", "api") else THIS_DIR
DATA_FILE = os.path.join(ROOT_DIR, "data", "merged_products_with_series.json")

# 全域快取（但不在 import 當下硬讀死）
PRODUCTS: List[dict] = []
LOAD_STATUS: str = "（尚未載入）"


# =========================
# 工具：數字安全轉換
# =========================
def _to_float(v: Any) -> float:
    try:
        return float(v)
    except:
        return 0.0


# =========================
# 讀取資料（可重載）
# =========================
def load_products(data_file: str = DATA_FILE) -> Dict[str, Any]:
    """
    讀取 JSON 後寫入全域 PRODUCTS。
    回傳 JSON 狀態（前端可顯示/可讀）。
    """
    global PRODUCTS, LOAD_STATUS

    if not os.path.exists(data_file):
        LOAD_STATUS = f"❌ 找不到資料檔：{data_file}"
        PRODUCTS = []
        return {"ok": False, "message": LOAD_STATUS, "data_file": data_file, "count": 0}

    try:
        with open(data_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            LOAD_STATUS = "❌ 檔案格式錯誤：最外層應為陣列(list)。"
            PRODUCTS = []
            return {"ok": False, "message": LOAD_STATUS, "data_file": data_file, "count": 0}

        # 可在此做最小正規化（避免前端拿到怪型態）
        normalized = []
        for p in data:
            if not isinstance(p, dict):
                continue
            normalized.append(p)

        PRODUCTS = normalized
        LOAD_STATUS = f"✅ 已載入 {len(PRODUCTS)} 筆資料。"
        return {"ok": True, "message": LOAD_STATUS, "data_file": data_file, "count": len(PRODUCTS)}

    except Exception as e:
        LOAD_STATUS = f"❌ 載入失敗：{e}"
        PRODUCTS = []
        return {"ok": False, "message": LOAD_STATUS, "data_file": data_file, "count": 0}


# =========================
# 系列關鍵字（放寬）匹配規則
# =========================
def _match_series_keyword(p: dict, series_keyword: str) -> bool:
    """
    放寬版：
    - 支援多關鍵字：用空白分隔（任一命中即 True）
    - 同時比對 series / model
    - 全部做 lower() 以免大小寫問題
    """
    q = (series_keyword or "").strip().lower()
    if not q:
        return True

    tokens = [t for t in q.split() if t]  # 例如：'米開朗 軌道' => ['米開朗','軌道']
    s = str(p.get("series", "")).lower()
    m = str(p.get("model", "")).lower()

    # 任一 token 命中 series 或 model 就算
    return any(t in s or t in m for t in tokens)


# =========================
# 篩選（回傳 JSON）
# =========================
def filter_products(
    series_keyword: str,
    watt_lo: float, watt_hi: float,
    cct_lo: float, cct_hi: float,
    beam_lo: float, beam_hi: float,
    lumen_lo: float, lumen_hi: float,
    price_lo: float, price_hi: float,
    topk: int
) -> Dict[str, Any]:
    """
    回傳給前端最友善的 JSON：
    {
      "ok": true/false,
      "query": {...},
      "total": N,
      "items": [ {series, model, watt, cct, ...}, ... ],
      "message": "..."
    }
    """
    if not PRODUCTS:
        return {"ok": False, "message": "尚未載入產品資料，請先載入/重載。", "total": 0, "items": []}

    # 1) 先做系列關鍵字模糊過濾
    base = [p for p in PRODUCTS if _match_series_keyword(p, series_keyword)]
    if series_keyword and series_keyword.strip() and not base:
        return {
            "ok": False,
            "message": f"找不到與「{series_keyword}」相關的系列/型號",
            "query": {"series_keyword": series_keyword},
            "total": 0,
            "items": []
        }

    # 2) 再做屬性篩選
    result = []
    for p in base:
        w  = _to_float(p.get("watt", 0))
        c  = _to_float(p.get("cct", 0))
        b  = _to_float(p.get("beam", 0))
        l  = _to_float(p.get("lumen", 0))
        pr = _to_float(p.get("price", 0))

        if not (watt_lo  <= w  <= watt_hi):   continue
        if not (cct_lo   <= c  <= cct_hi):    continue
        if not (beam_lo  <= b  <= beam_hi):   continue
        if not (lumen_lo <= l  <= lumen_hi):  continue
        if not (price_lo <= pr <= price_hi):  continue

        result.append({
            "series": p.get("series", ""),
            "model": p.get("model", ""),
            "watt": w,
            "cct": c,
            "beam": b,
            "lumen": l,
            "price": pr,
            "voltage": p.get("voltage", ""),
            "cri": p.get("cri", ""),
            "ip": p.get("ip", ""),
            "price_from": p.get("price_from", "")
        })

    if not result:
        msg = f"系列關鍵字「{series_keyword}」下沒有符合屬性條件的產品。" if series_keyword and series_keyword.strip() else "沒有任何產品符合屬性條件。"
        return {"ok": False, "message": msg, "query": {"series_keyword": series_keyword}, "total": 0, "items": []}

    # 3) TopK 截斷（你也可以在這裡加排序規則）
    result = result[: int(topk)]

    return {
        "ok": True,
        "message": "success",
        "query": {
            "series_keyword": series_keyword,
            "watt": [watt_lo, watt_hi],
            "cct": [cct_lo, cct_hi],
            "beam": [beam_lo, beam_hi],
            "lumen": [lumen_lo, lumen_hi],
            "price": [price_lo, price_hi],
            "topk": int(topk),
        },
        "total": len(result),
        "items": result
    }


# =========================
# Gradio UI（展示/測試）
# - 後端給組員串：直接用 filter_products() 回傳 JSON
# =========================
def _ensure_loaded():
    # UI 開啟時自動載入一次（若檔案不存在，也會回錯誤 JSON）
    return load_products(DATA_FILE)

with gr.Blocks(title="燈具系列篩選系統（後端友善版）") as demo:
    gr.Markdown("# 💡 燈具系列 → 型號篩選系統（後端友善版）")
    gr.Markdown("資料來源：`data/merged_products_with_series.json`")

    with gr.Row():
        btn_reload = gr.Button("🔄 重載資料", variant="secondary")
        status_json = gr.JSON(label="載入狀態")

    # 自動載入一次
    demo.load(_ensure_loaded, outputs=[status_json])
    btn_reload.click(lambda: load_products(DATA_FILE), outputs=[status_json])

    gr.Markdown("## 🧾 系列關鍵字（模糊）＋屬性篩選")
    series_input = gr.Textbox(
        label="系列關鍵字（可留空 / 可多關鍵字）",
        placeholder="例如：排燈、米開朗、軌道；或輸入「米開朗 軌道」(空白分隔，多關鍵字任一命中)"
    )

    with gr.Row():
        watt_lo = gr.Slider(0, 200, 0, step=1, label="功率最小 (W)")
        watt_hi = gr.Slider(0, 200, 200, step=1, label="功率最大 (W)")
    with gr.Row():
        cct_lo = gr.Slider(2000, 7000, 2700, step=50, label="色溫最小 (K)")
        cct_hi = gr.Slider(2000, 7000, 6500, step=50, label="色溫最大 (K)")
    with gr.Row():
        beam_lo = gr.Slider(0, 120, 0, step=1, label="光束角最小 (°)")
        beam_hi = gr.Slider(0, 120, 120, step=1, label="光束角最大 (°)")
    with gr.Row():
        lumen_lo = gr.Slider(0, 15000, 0, step=10, label="光通量最小 (lm)")
        lumen_hi = gr.Slider(0, 15000, 15000, step=10, label="光通量最大 (lm)")
    with gr.Row():
        price_lo = gr.Slider(0, 200000, 0, step=100, label="價格最小")
        price_hi = gr.Slider(0, 200000, 200000, step=100, label="價格最大")
    topk = gr.Slider(1, 200, 50, step=1, label="最多顯示筆數")

    btn_filter = gr.Button("開始篩選", variant="primary")
    result_json = gr.JSON(label="篩選結果（給前端串接用）")

    btn_filter.click(
        filter_products,
        inputs=[
            series_input,
            watt_lo, watt_hi,
            cct_lo, cct_hi,
            beam_lo, beam_hi,
            lumen_lo, lumen_hi,
            price_lo, price_hi,
            topk
        ],
        outputs=[result_json]
    )

if __name__ == "__main__":
    demo.launch()
