"""
Generate synthetic engineering drawing PDFs for the Drawing Extraction App.
Each PDF mimics a real mechanical engineering drawing with:
- Title block (in the drawing's language)
- Dimensioned orthographic views (front + side)
- Tolerance block (ISO 2768)
- Optional BOM table
"""

import json
import math
import os
from io import BytesIO

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch
import numpy as np

from reportlab.lib.pagesizes import A3, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.colors import black, white, HexColor

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# Language packs for title block labels
# ---------------------------------------------------------------------------
LANG_PACKS = {
    "en": {
        "description": "DESCRIPTION",
        "material": "MATERIAL",
        "finish": "SURFACE TREATMENT",
        "weight": "WEIGHT",
        "scale": "SCALE",
        "designer": "DESIGNER",
        "date": "DATE",
        "revision": "REV",
        "part_number": "PART NUMBER",
        "sheet": "SHEET",
        "tolerance_title": "TOLERANCES PER ISO 2768-mK",
        "pos": "POS.",
        "bom_desc": "DESCRIPTION",
        "bom_mat": "MATERIAL",
        "bom_qty": "QTY",
        "cosmetic": "COSMETIC REQ.",
        "format": "FORMAT",
    },
    "it": {
        "description": "DESCRIZIONE",
        "material": "MATERIALE",
        "finish": "TIPO TRATTAMENTO",
        "weight": "PESO Kg",
        "scale": "SCALA",
        "designer": "Progettista",
        "date": "Data Creazione",
        "revision": "REV N.",
        "part_number": "CODICE",
        "sheet": "NR. FOGLI",
        "tolerance_title": "TOLLERANZE SECONDO ISO 2768-cL",
        "pos": "POS.",
        "bom_desc": "DESCRIZIONE",
        "bom_mat": "MATERIALE",
        "bom_qty": "Q.TA'",
        "cosmetic": "REQUISITI COSMETICI",
        "format": "FORMATO",
    },
    "de": {
        "description": "BEZEICHNUNG",
        "material": "WERKSTOFF",
        "finish": "OBERFLÄCHENBEHANDLUNG",
        "weight": "GEWICHT",
        "scale": "MASSSTAB",
        "designer": "Konstrukteur",
        "date": "Datum",
        "revision": "ÄND.",
        "part_number": "ZEICHNUNGSNR.",
        "sheet": "BLATT",
        "tolerance_title": "TOLERANZEN NACH ISO 2768-mK",
        "pos": "POS.",
        "bom_desc": "BENENNUNG",
        "bom_mat": "WERKSTOFF",
        "bom_qty": "MENGE",
        "cosmetic": "KOSMETISCHE ANFORDERUNG",
        "format": "FORMAT",
    },
    "fr": {
        "description": "DÉSIGNATION",
        "material": "MATÉRIAU",
        "finish": "TRAITEMENT DE SURFACE",
        "weight": "POIDS",
        "scale": "ÉCHELLE",
        "designer": "Concepteur",
        "date": "Date",
        "revision": "RÉV.",
        "part_number": "NUMÉRO DE PIÈCE",
        "sheet": "FEUILLE",
        "tolerance_title": "TOLÉRANCES SELON ISO 2768-mK",
        "pos": "POS.",
        "bom_desc": "DÉSIGNATION",
        "bom_mat": "MATÉRIAU",
        "bom_qty": "QTÉ",
        "cosmetic": "EXIGENCE COSMÉTIQUE",
        "format": "FORMAT",
    },
    "es": {
        "description": "DESCRIPCIÓN",
        "material": "MATERIAL",
        "finish": "TRATAMIENTO SUPERFICIAL",
        "weight": "PESO",
        "scale": "ESCALA",
        "designer": "Diseñador",
        "date": "Fecha",
        "revision": "REV.",
        "part_number": "NÚMERO DE PIEZA",
        "sheet": "HOJA",
        "tolerance_title": "TOLERANCIAS SEGÚN ISO 2768-mK",
        "pos": "POS.",
        "bom_desc": "DESCRIPCIÓN",
        "bom_mat": "MATERIAL",
        "bom_qty": "CANT.",
        "cosmetic": "REQUISITO COSMÉTICO",
        "format": "FORMATO",
    },
}


# ---------------------------------------------------------------------------
# Drawing specifications
# ---------------------------------------------------------------------------
DRAWINGS = [
    {
        "filename": "EN_bracket_assy.pdf",
        "lang": "en",
        "part_number": "BRK-20240101",
        "part_name": "Mounting bracket assembly",
        "revision": "02",
        "material": "AL6061-T6",
        "finish": "ANODIZE BLACK",
        "cosmetic": None,  # intentionally missing
        "weight_kg": 1.85,
        "scale": "2:1",
        "designer": "J. Smith",
        "date": "2024-01-15",
        "dims": {
            "front": {"w": 120, "h": 80, "features": [
                {"type": "rect", "x": 10, "y": 10, "w": 100, "h": 60},
                {"type": "hole", "cx": 25, "cy": 40, "r": 5},
                {"type": "hole", "cx": 95, "cy": 40, "r": 5},
            ]},
            "side": {"w": 40, "h": 80, "features": [
                {"type": "rect", "x": 5, "y": 10, "w": 30, "h": 60},
            ]},
        },
        "critical_dimensions": [
            {"value": "120 mm", "tolerance": "±0.5", "location": "Overall width", "evidence": "\"120\" on front view"},
            {"value": "80 mm", "tolerance": "±0.5", "location": "Overall height", "evidence": "\"80\" on front view"},
            {"value": "40 mm", "tolerance": "±0.3", "location": "Depth", "evidence": "\"40\" on side view"},
            {"value": "Ø10 (2x)", "tolerance": "H7", "location": "Mounting holes", "evidence": "\"Ø10(2x)\" on front view"},
            {"value": "70 mm", "tolerance": "±0.2", "location": "Hole spacing", "evidence": "\"70\" between holes"},
        ],
        "bbox": {"x": 120, "y": 80, "z": 40, "source": "Overall dims from front + side views"},
        "bom": None,
        "missing_fields": ["cosmetic_requirement"],
    },
    {
        "filename": "DE_kabelrinne_platte.pdf",
        "lang": "de",
        "part_number": "KRP-30050200",
        "part_name": "KABELRINNENPLATTE",
        "part_name_en": "Cable tray plate",
        "revision": "01",
        "material": "S355J2",
        "finish": None,  # intentionally missing
        "cosmetic": None,  # intentionally missing
        "weight_kg": 8.42,
        "scale": "1:2",
        "designer": "H. Müller",
        "date": "2023-11-20",
        "dims": {
            "front": {"w": 300, "h": 150, "features": [
                {"type": "rect", "x": 0, "y": 0, "w": 300, "h": 150},
                {"type": "hole", "cx": 30, "cy": 30, "r": 7},
                {"type": "hole", "cx": 270, "cy": 30, "r": 7},
                {"type": "hole", "cx": 30, "cy": 120, "r": 7},
                {"type": "hole", "cx": 270, "cy": 120, "r": 7},
                {"type": "slot", "x": 120, "y": 60, "w": 60, "h": 30},
            ]},
            "side": {"w": 8, "h": 150, "features": [
                {"type": "rect", "x": 0, "y": 0, "w": 8, "h": 150},
            ]},
        },
        "critical_dimensions": [
            {"value": "300 mm", "tolerance": "±1.0", "location": "Gesamtlänge", "evidence": "\"300\" Vorderansicht"},
            {"value": "150 mm", "tolerance": "±0.8", "location": "Gesamtbreite", "evidence": "\"150\" Vorderansicht"},
            {"value": "8 mm", "tolerance": "±0.3", "location": "Blechstärke", "evidence": "\"8\" Seitenansicht"},
            {"value": "Ø14 (4x)", "tolerance": "H9", "location": "Befestigungslöcher", "evidence": "\"Ø14(4x)\" Vorderansicht"},
            {"value": "60 x 30", "tolerance": "±0.5", "location": "Schlitz Mitte", "evidence": "\"60 x 30\" Schlitz"},
        ],
        "bbox": {"x": 300, "y": 150, "z": 8, "source": "Abmessungen aus Vorder- und Seitenansicht"},
        "bom": [
            {"pos": 1, "desc": "BLECH 8mm 300x150", "mat": "S355J2", "qty": 1},
            {"pos": 2, "desc": "SECHSKANTSCHRAUBE M12x30", "mat": "8.8 VERZINKT", "qty": 4},
            {"pos": 3, "desc": "UNTERLEGSCHEIBE M12", "mat": "STAHL VERZINKT", "qty": 4},
        ],
        "missing_fields": ["finish", "cosmetic_requirement"],
    },
    {
        "filename": "FR_gousset.pdf",
        "lang": "fr",
        "part_number": "GS-FR-44210",
        "part_name": "GOUSSET DE RENFORT",
        "part_name_en": "Reinforcement gusset",
        "revision": "00",
        "material": "S235JR",
        "finish": "GALVANISATION À CHAUD",
        "cosmetic": "CLASSE B - AUCUNE RAYURE VISIBLE",
        "weight_kg": 2.15,
        "scale": "1:1",
        "designer": "P. Dupont",
        "date": "2024-03-08",
        "dims": {
            "front": {"w": 150, "h": 150, "features": [
                {"type": "triangle", "points": [(0, 0), (150, 0), (0, 150)]},
                {"type": "hole", "cx": 30, "cy": 30, "r": 6.5},
                {"type": "hole", "cx": 30, "cy": 100, "r": 6.5},
                {"type": "hole", "cx": 100, "cy": 30, "r": 6.5},
            ]},
            "side": {"w": 10, "h": 150, "features": [
                {"type": "rect", "x": 0, "y": 0, "w": 10, "h": 150},
            ]},
        },
        "critical_dimensions": [
            {"value": "150 mm", "tolerance": "±0.5", "location": "Côté du triangle", "evidence": "\"150\" vue de face"},
            {"value": "10 mm", "tolerance": "±0.3", "location": "Épaisseur", "evidence": "\"10\" vue latérale"},
            {"value": "Ø13 (3x)", "tolerance": "H9", "location": "Trous de montage", "evidence": "\"Ø13(3x)\" vue de face"},
            {"value": "70 mm", "tolerance": "±0.3", "location": "Entraxe vertical", "evidence": "\"70\" entre trous"},
            {"value": "70 mm", "tolerance": "±0.3", "location": "Entraxe horizontal", "evidence": "\"70\" entre trous"},
        ],
        "bbox": {"x": 150, "y": 150, "z": 10, "source": "Dimensions d'encombrement"},
        "bom": None,
        "missing_fields": [],
    },
    {
        "filename": "EN_shaft_adapter.pdf",
        "lang": "en",
        "part_number": "SA-EN-78500",
        "part_name": "Shaft adapter sleeve",
        "revision": "03",
        "material": None,  # intentionally missing
        "finish": "PASSIVATE PER QQ-P-35",
        "cosmetic": "CLASS A - NO TOOL MARKS",
        "weight_kg": 0.45,
        "scale": "5:1",
        "designer": "R. Chen",
        "date": "2024-06-12",
        "dims": {
            "front": {"w": 60, "h": 60, "features": [
                {"type": "circle", "cx": 30, "cy": 30, "r": 30},
                {"type": "circle", "cx": 30, "cy": 30, "r": 15},
                {"type": "hole", "cx": 30, "cy": 5, "r": 2.5},
                {"type": "hole", "cx": 30, "cy": 55, "r": 2.5},
            ]},
            "side": {"w": 45, "h": 60, "features": [
                {"type": "rect", "x": 0, "y": 5, "w": 45, "h": 50},
                {"type": "rect", "x": 5, "y": 10, "w": 35, "h": 40},
            ]},
        },
        "critical_dimensions": [
            {"value": "Ø60 mm", "tolerance": "h6", "location": "Outer diameter", "evidence": "\"Ø60\" on front view"},
            {"value": "Ø30 mm", "tolerance": "H7", "location": "Inner bore", "evidence": "\"Ø30\" on front view"},
            {"value": "45 mm", "tolerance": "±0.1", "location": "Length", "evidence": "\"45\" on side view"},
            {"value": "Ø5 (2x)", "tolerance": "±0.05", "location": "Set screw holes", "evidence": "\"Ø5(2x)\" on front view"},
            {"value": "0.8 µm Ra", "tolerance": None, "location": "Bore surface", "evidence": "Surface finish symbol on bore"},
        ],
        "bbox": {"x": 60, "y": 60, "z": 45, "source": "Ø60 envelope + 45 length"},
        "bom": None,
        "missing_fields": ["material"],
    },
    {
        "filename": "IT_telaio_saldato.pdf",
        "lang": "it",
        "part_number": "TLS-IT-90200",
        "part_name": "TELAIO SALDATO PER QUADRO ELETTRICO",
        "part_name_en": "Welded frame for electrical panel",
        "revision": "01",
        "material": "S235JR",
        "finish": "VERNICIATURA RAL 7035",
        "cosmetic": "CLASSE A - NESSUN SEGNO VISIBILE",
        "weight_kg": 45.80,
        "scale": "1:5",
        "designer": "M. Rossi",
        "date": "2024-02-28",
        "dims": {
            "front": {"w": 800, "h": 600, "features": [
                {"type": "rect", "x": 0, "y": 0, "w": 800, "h": 600},
                {"type": "rect", "x": 40, "y": 40, "w": 720, "h": 520},
                {"type": "hole", "cx": 20, "cy": 20, "r": 7},
                {"type": "hole", "cx": 780, "cy": 20, "r": 7},
                {"type": "hole", "cx": 20, "cy": 580, "r": 7},
                {"type": "hole", "cx": 780, "cy": 580, "r": 7},
            ]},
            "side": {"w": 200, "h": 600, "features": [
                {"type": "rect", "x": 0, "y": 0, "w": 200, "h": 600},
                {"type": "rect", "x": 40, "y": 40, "w": 120, "h": 520},
            ]},
        },
        "critical_dimensions": [
            {"value": "800 mm", "tolerance": "±2.0", "location": "Larghezza totale", "evidence": "\"800\" vista frontale"},
            {"value": "600 mm", "tolerance": "±2.0", "location": "Altezza totale", "evidence": "\"600\" vista frontale"},
            {"value": "200 mm", "tolerance": "±1.0", "location": "Profondità", "evidence": "\"200\" vista laterale"},
            {"value": "Ø14 (4x)", "tolerance": "H9", "location": "Fori angolari", "evidence": "\"Ø14(4x)\" agli angoli"},
            {"value": "40 mm", "tolerance": "±0.5", "location": "Spessore telaio", "evidence": "\"40\" profilo del telaio"},
        ],
        "bbox": None,  # intentionally missing
        "bom": [
            {"pos": 1, "desc": "PROFILO TUBOLARE 40x40x3 L=800", "mat": "S235JR", "qty": 2},
            {"pos": 2, "desc": "PROFILO TUBOLARE 40x40x3 L=520", "mat": "S235JR", "qty": 2},
            {"pos": 3, "desc": "PROFILO TUBOLARE 40x40x3 L=120", "mat": "S235JR", "qty": 4},
            {"pos": 4, "desc": "LAMIERA SP.2 800x600", "mat": "S235JR", "qty": 1},
            {"pos": 5, "desc": "CERNIERA 80mm", "mat": "ACCIAIO ZINCATO", "qty": 3},
            {"pos": 6, "desc": "CHIUSURA A LEVA", "mat": "ACCIAIO ZINCATO", "qty": 2},
        ],
        "missing_fields": ["bounding_box"],
    },
    {
        "filename": "ES_placa_cubierta.pdf",
        "lang": "es",
        "part_number": "PC-ES-55100",
        "part_name": "PLACA DE CUBIERTA",
        "part_name_en": "Cover plate",
        "revision": "00",
        "material": None,  # intentionally missing
        "finish": None,  # intentionally missing
        "cosmetic": None,
        "weight_kg": 0.95,
        "scale": "1:1",
        "designer": "C. García",
        "date": "2024-04-20",
        "dims": {
            "front": {"w": 200, "h": 120, "features": [
                {"type": "rect", "x": 0, "y": 0, "w": 200, "h": 120},
                {"type": "rect", "x": 20, "y": 20, "w": 160, "h": 80, "style": "dashed"},
                {"type": "hole", "cx": 10, "cy": 10, "r": 3.5},
                {"type": "hole", "cx": 190, "cy": 10, "r": 3.5},
                {"type": "hole", "cx": 10, "cy": 110, "r": 3.5},
                {"type": "hole", "cx": 190, "cy": 110, "r": 3.5},
            ]},
            "side": {"w": 3, "h": 120, "features": [
                {"type": "rect", "x": 0, "y": 0, "w": 3, "h": 120},
            ]},
        },
        "critical_dimensions": [
            {"value": "200 mm", "tolerance": "±0.5", "location": "Longitud total", "evidence": "\"200\" vista frontal"},
            {"value": "120 mm", "tolerance": "±0.5", "location": "Ancho total", "evidence": "\"120\" vista frontal"},
            {"value": "3 mm", "tolerance": "±0.2", "location": "Espesor", "evidence": "\"3\" vista lateral"},
            {"value": "Ø7 (4x)", "tolerance": "H9", "location": "Agujeros de montaje", "evidence": "\"Ø7(4x)\" esquinas"},
            {"value": "160 x 80", "tolerance": "±0.5", "location": "Ventana de acceso", "evidence": "\"160 x 80\" rectángulo central"},
        ],
        "bbox": {"x": 200, "y": 120, "z": 3, "source": "Dimensiones de envolvente"},
        "bom": None,
        "missing_fields": ["material", "finish", "cosmetic_requirement"],
    },
    {
        "filename": "EN_sensor_mount_degraded.pdf",
        "lang": "en",
        "part_number": "SM-EN-66300",
        "part_name": "Sensor mounting plate",
        "revision": "01",
        "material": "SS304",
        "finish": "ELECTROPOLISH",
        "cosmetic": "CLASS A - FOOD GRADE",
        "weight_kg": 0.32,
        "scale": "2:1",
        "designer": "A. Patel",
        "date": "2023-09-05",
        "dims": {
            "front": {"w": 80, "h": 50, "features": [
                {"type": "rect", "x": 0, "y": 0, "w": 80, "h": 50},
                {"type": "hole", "cx": 15, "cy": 25, "r": 4},
                {"type": "hole", "cx": 65, "cy": 25, "r": 4},
                {"type": "slot", "x": 30, "y": 15, "w": 20, "h": 20},
            ]},
            "side": {"w": 6, "h": 50, "features": [
                {"type": "rect", "x": 0, "y": 0, "w": 6, "h": 50},
            ]},
        },
        "critical_dimensions": [
            {"value": "80 mm", "tolerance": "±0.3", "location": "Overall length", "evidence": "\"80\" front view"},
            {"value": "50 mm", "tolerance": "±0.3", "location": "Overall width", "evidence": "\"50\" front view"},
            {"value": "6 mm", "tolerance": "±0.1", "location": "Thickness", "evidence": "\"6\" side view"},
            {"value": "Ø8 (2x)", "tolerance": "H7", "location": "Mounting holes", "evidence": "\"Ø8(2x)\" front view"},
            {"value": "20 x 20", "tolerance": "±0.2", "location": "Sensor cutout", "evidence": "\"20 x 20\" central slot"},
        ],
        "bbox": {"x": 80, "y": 50, "z": 6, "source": "Overall dims from front + side views"},
        "bom": None,
        "missing_fields": [],
        "degraded": True,
    },
]


def draw_engineering_view(dwg_spec, view_type="front"):
    """Render a simplified engineering view as a matplotlib figure, return PNG bytes."""
    view = dwg_spec["dims"][view_type]
    w, h = view["w"], view["h"]

    # Scale to reasonable figure size
    max_dim = max(w, h)
    scale = 4.0 / max_dim  # target ~4 inches
    fig_w = max(w * scale + 1.5, 2.5)
    fig_h = max(h * scale + 1.5, 2.5)

    fig, ax = plt.subplots(1, 1, figsize=(fig_w, fig_h))
    ax.set_xlim(-0.15 * w, w * 1.25)
    ax.set_ylim(-0.15 * h, h * 1.25)
    ax.set_aspect("equal")
    ax.axis("off")

    degraded = dwg_spec.get("degraded", False)
    lw = 1.5 if not degraded else 1.0
    text_color = "black" if not degraded else "#444444"

    for feat in view["features"]:
        if feat["type"] == "rect":
            style = feat.get("style", "solid")
            ls = "--" if style == "dashed" else "-"
            rect = mpatches.FancyBboxPatch(
                (feat["x"], feat["y"]), feat["w"], feat["h"],
                linewidth=lw, edgecolor="black", facecolor="none",
                linestyle=ls, boxstyle="square,pad=0"
            )
            ax.add_patch(rect)
        elif feat["type"] == "hole":
            circle = plt.Circle((feat["cx"], feat["cy"]), feat["r"],
                                linewidth=lw, edgecolor="black", facecolor="none")
            ax.add_patch(circle)
            # Crosshair
            r = feat["r"]
            ax.plot([feat["cx"] - r * 0.7, feat["cx"] + r * 0.7],
                    [feat["cy"], feat["cy"]], color="black", lw=0.5)
            ax.plot([feat["cx"], feat["cx"]],
                    [feat["cy"] - r * 0.7, feat["cy"] + r * 0.7], color="black", lw=0.5)
        elif feat["type"] == "circle":
            circle = plt.Circle((feat["cx"], feat["cy"]), feat["r"],
                                linewidth=lw, edgecolor="black", facecolor="none")
            ax.add_patch(circle)
        elif feat["type"] == "triangle":
            pts = feat["points"]
            triangle = plt.Polygon(pts, linewidth=lw, edgecolor="black", facecolor="none")
            ax.add_patch(triangle)
        elif feat["type"] == "slot":
            rect = mpatches.FancyBboxPatch(
                (feat["x"], feat["y"]), feat["w"], feat["h"],
                linewidth=lw, edgecolor="black", facecolor="none",
                boxstyle="round,pad=0,rounding_size=3"
            )
            ax.add_patch(rect)

    # Add some dimension lines
    offset = max_dim * 0.08
    # Width dimension (bottom)
    ax.annotate("", xy=(w, -offset), xytext=(0, -offset),
                arrowprops=dict(arrowstyle="<->", color="red", lw=0.8))
    ax.text(w / 2, -offset - max_dim * 0.04, str(w), ha="center", va="top",
            fontsize=8, color=text_color, fontweight="bold")

    # Height dimension (left)
    ax.annotate("", xy=(-offset, h), xytext=(-offset, 0),
                arrowprops=dict(arrowstyle="<->", color="red", lw=0.8))
    ax.text(-offset - max_dim * 0.04, h / 2, str(h), ha="right", va="center",
            fontsize=8, color=text_color, fontweight="bold", rotation=90)

    # Add hole callouts for first 2 holes
    holes = [f for f in view["features"] if f["type"] == "hole"]
    for i, hole in enumerate(holes[:2]):
        r = hole["r"]
        diam = r * 2
        count = sum(1 for h2 in holes if abs(h2["r"] - r) < 0.01)
        label = f"Ø{diam:.0f}" if count <= 1 else f"Ø{diam:.0f}({count}x)"
        ax.annotate(label, xy=(hole["cx"] + r, hole["cy"]),
                    xytext=(hole["cx"] + r + max_dim * 0.1, hole["cy"] + max_dim * 0.08),
                    fontsize=7, color=text_color, fontweight="bold",
                    arrowprops=dict(arrowstyle="->", color="black", lw=0.6))

    if degraded:
        # Add noise/artifacts to simulate degraded scan
        np.random.seed(42)
        for _ in range(50):
            x = np.random.uniform(-0.1 * w, w * 1.1)
            y = np.random.uniform(-0.1 * h, h * 1.1)
            ax.plot(x, y, ".", color="#999999", markersize=np.random.uniform(0.5, 2))

    fig.tight_layout(pad=0.3)

    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def create_drawing_pdf(dwg):
    """Create a complete engineering drawing PDF."""
    lang = LANG_PACKS[dwg["lang"]]
    filepath = os.path.join(OUTPUT_DIR, dwg["filename"])
    page_w, page_h = landscape(A3)

    c = canvas.Canvas(filepath, pagesize=landscape(A3))
    c.setTitle(f"{dwg['part_number']} - {dwg['part_name']}")

    # Border
    margin = 10 * mm
    c.setStrokeColor(black)
    c.setLineWidth(2)
    c.rect(margin, margin, page_w - 2 * margin, page_h - 2 * margin)
    c.setLineWidth(0.5)
    c.rect(margin + 2 * mm, margin + 2 * mm,
           page_w - 2 * margin - 4 * mm, page_h - 2 * margin - 4 * mm)

    # ---- Title Block (bottom right) ----
    tb_w = 180 * mm
    tb_h = 55 * mm
    tb_x = page_w - margin - tb_w - 3 * mm
    tb_y = margin + 3 * mm

    c.setLineWidth(1)
    c.rect(tb_x, tb_y, tb_w, tb_h)

    # Grid lines
    row_h = tb_h / 5
    for i in range(1, 5):
        c.line(tb_x, tb_y + i * row_h, tb_x + tb_w, tb_y + i * row_h)
    col_w = tb_w / 3
    for i in range(1, 3):
        c.line(tb_x + i * col_w, tb_y, tb_x + i * col_w, tb_y + tb_h)

    c.setFont("Helvetica", 6)

    # Row 0 (bottom): Part number + revision
    c.drawString(tb_x + 3, tb_y + 3, f"{lang['part_number']}:")
    c.setFont("Helvetica-Bold", 10)
    c.drawString(tb_x + 3, tb_y + 12, dwg["part_number"])
    c.setFont("Helvetica", 6)
    c.drawString(tb_x + col_w + 3, tb_y + 3, f"{lang['revision']}:")
    c.setFont("Helvetica-Bold", 10)
    c.drawString(tb_x + col_w + 3, tb_y + 12, dwg["revision"])
    c.setFont("Helvetica", 6)
    c.drawString(tb_x + 2 * col_w + 3, tb_y + 3, f"{lang['format']}:")
    c.drawString(tb_x + 2 * col_w + 3, tb_y + 12, "A3")

    # Row 1: Description
    y1 = tb_y + row_h
    c.drawString(tb_x + 3, y1 + 3, f"{lang['description']}:")
    c.setFont("Helvetica-Bold", 8)
    c.drawString(tb_x + 3, y1 + 14, dwg["part_name"])
    c.setFont("Helvetica", 6)

    # Row 2: Material + Finish
    y2 = tb_y + 2 * row_h
    c.drawString(tb_x + 3, y2 + 3, f"{lang['material']}:")
    if dwg["material"]:
        c.setFont("Helvetica-Bold", 8)
        c.drawString(tb_x + 3, y2 + 14, dwg["material"])
        c.setFont("Helvetica", 6)

    c.drawString(tb_x + col_w + 3, y2 + 3, f"{lang['finish']}:")
    if dwg["finish"]:
        c.setFont("Helvetica-Bold", 7)
        c.drawString(tb_x + col_w + 3, y2 + 14, dwg["finish"])
        c.setFont("Helvetica", 6)

    # Row 3: Weight + Scale + Designer
    y3 = tb_y + 3 * row_h
    c.drawString(tb_x + 3, y3 + 3, f"{lang['weight']}:")
    c.drawString(tb_x + 3, y3 + 14, f"{dwg['weight_kg']}")
    c.drawString(tb_x + col_w + 3, y3 + 3, f"{lang['scale']}:")
    c.drawString(tb_x + col_w + 3, y3 + 14, dwg["scale"])
    c.drawString(tb_x + 2 * col_w + 3, y3 + 3, f"{lang['sheet']}:")
    c.drawString(tb_x + 2 * col_w + 3, y3 + 14, "1 / 1")

    # Row 4 (top): Designer + Date + Cosmetic
    y4 = tb_y + 4 * row_h
    c.drawString(tb_x + 3, y4 + 3, f"{lang['designer']}:")
    c.drawString(tb_x + 3, y4 + 14, dwg["designer"])
    c.drawString(tb_x + col_w + 3, y4 + 3, f"{lang['date']}:")
    c.drawString(tb_x + col_w + 3, y4 + 14, dwg["date"])
    if dwg.get("cosmetic"):
        c.drawString(tb_x + 2 * col_w + 3, y4 + 3, f"{lang['cosmetic']}:")
        c.setFont("Helvetica", 5)
        c.drawString(tb_x + 2 * col_w + 3, y4 + 14, dwg["cosmetic"])
        c.setFont("Helvetica", 6)

    # ---- Tolerance block (bottom left) ----
    tol_x = margin + 3 * mm
    tol_y = margin + 3 * mm
    tol_w = 90 * mm
    tol_h = 35 * mm
    c.setLineWidth(0.5)
    c.rect(tol_x, tol_y, tol_w, tol_h)
    c.setFont("Helvetica-Bold", 6)
    c.drawString(tol_x + 3, tol_y + tol_h - 10, lang["tolerance_title"])
    c.setFont("Helvetica", 5)
    # Simplified tolerance table
    tol_data = [
        "LINEAR:  ≤6: ±0.1  ≤30: ±0.2  ≤120: ±0.3  ≤400: ±0.5  ≤1000: ±0.8",
        "ANGULAR: ≤10: ±1°  ≤50: ±0°30'  ≤120: ±0°20'  >120: ±0°10'",
        "ALL DIMENSIONS IN mm UNLESS OTHERWISE STATED",
    ]
    for i, line in enumerate(tol_data):
        c.drawString(tol_x + 3, tol_y + tol_h - 20 - i * 8, line)

    # ---- BOM table (if applicable) ----
    if dwg.get("bom"):
        bom = dwg["bom"]
        bom_x = margin + 3 * mm
        bom_y = page_h - margin - 3 * mm - (len(bom) + 1) * 7 * mm
        bom_w = 160 * mm
        bom_row_h = 7 * mm
        bom_cols = [10 * mm, 90 * mm, 40 * mm, 20 * mm]

        c.setLineWidth(0.5)
        # Header
        c.setFillColor(HexColor("#e0e0e0"))
        c.rect(bom_x, bom_y + len(bom) * bom_row_h, bom_w, bom_row_h, fill=1)
        c.setFillColor(black)
        c.setFont("Helvetica-Bold", 7)
        headers = [lang["pos"], lang["bom_desc"], lang["bom_mat"], lang["bom_qty"]]
        cx = bom_x
        for j, (hdr, cw) in enumerate(zip(headers, bom_cols)):
            c.drawString(cx + 2, bom_y + len(bom) * bom_row_h + 2, hdr)
            cx += cw

        # Rows
        c.setFont("Helvetica", 7)
        for i, item in enumerate(bom):
            y = bom_y + (len(bom) - 1 - i) * bom_row_h
            c.rect(bom_x, y, bom_w, bom_row_h)
            cx = bom_x
            vals = [str(item["pos"]), item["desc"], item["mat"], str(item["qty"])]
            for val, cw in zip(vals, bom_cols):
                c.drawString(cx + 2, y + 2, val)
                cx += cw

    # ---- Engineering views (rendered as images) ----
    # Front view
    front_png = draw_engineering_view(dwg, "front")
    from reportlab.lib.utils import ImageReader
    front_img = ImageReader(BytesIO(front_png))
    img_w = 200 * mm
    img_h = 150 * mm
    view_x = margin + 100 * mm
    view_y = tb_y + tb_h + 20 * mm
    c.drawImage(front_img, view_x, view_y, width=img_w, height=img_h,
                preserveAspectRatio=True, anchor="sw")

    # View label
    c.setFont("Helvetica-Bold", 8)
    c.drawString(view_x + img_w / 2 - 20, view_y - 5 * mm, "FRONT VIEW")

    # Side view
    side_png = draw_engineering_view(dwg, "side")
    side_img = ImageReader(BytesIO(side_png))
    side_x = view_x + img_w + 15 * mm
    c.drawImage(side_img, side_x, view_y, width=80 * mm, height=img_h,
                preserveAspectRatio=True, anchor="sw")
    c.drawString(side_x + 20 * mm, view_y - 5 * mm, "SIDE VIEW")

    c.save()
    print(f"  Created: {dwg['filename']}")


def generate_ground_truth():
    """Generate ground truth JSON for all drawings."""
    truth = {}
    for dwg in DRAWINGS:
        entry = {
            "file_name": dwg["filename"],
            "source_language": dwg["lang"],
            "part_number": dwg["part_number"],
            "part_name_original": dwg["part_name"],
            "part_name_en": dwg.get("part_name_en", dwg["part_name"]),
            "revision": dwg["revision"],
            "material": dwg["material"],
            "finish": dwg["finish"],
            "cosmetic_requirement": dwg.get("cosmetic"),
            "weight_kg": dwg["weight_kg"],
            "critical_dimensions": dwg["critical_dimensions"],
            "bounding_box": dwg["bbox"],
            "bom": dwg.get("bom"),
            "missing_fields": dwg["missing_fields"],
        }
        truth[dwg["part_number"]] = entry

    path = os.path.join(OUTPUT_DIR, "ground_truth.json")
    with open(path, "w") as f:
        json.dump(truth, f, indent=2, ensure_ascii=False)
    print(f"  Created: ground_truth.json")


if __name__ == "__main__":
    print("Generating synthetic engineering drawings...")
    for dwg in DRAWINGS:
        create_drawing_pdf(dwg)
    generate_ground_truth()
    print(f"\nDone! {len(DRAWINGS)} drawings + ground_truth.json in {OUTPUT_DIR}")
