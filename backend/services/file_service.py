import os
import re
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")


def ensure_upload_dir():
    Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)


def sanitize_filename(name: str) -> str:
    name = re.sub(r'[^\w\u4e00-\u9fff\-_.]', '_', name)
    return name[:80]


def generate_markdown_file(
    task_id: int,
    agent_type: str,
    brand_name: str,
    content: str,
) -> tuple[str, str]:
    """Generate .md file and return (file_path, file_name)"""
    ensure_upload_dir()
    agent_names = {"strategy": "战略规划", "brand": "品牌设计", "operations": "运营实施"}
    agent_name = agent_names.get(agent_type, agent_type)
    safe_brand = sanitize_filename(brand_name or "品牌")
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    file_name = f"{safe_brand}_{agent_name}_{timestamp}.md"
    file_path = os.path.join(UPLOAD_DIR, file_name)

    header = f"# {brand_name or '品牌'} - {agent_name}方案\n\n"
    header += f"> 生成时间：{datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}\n\n"
    header += f"> 本方案由AI专家生成，仅供参考\n\n---\n\n"

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(header + content)

    return file_path, file_name


def generate_pdf_file(
    task_id: int,
    agent_type: str,
    brand_name: str,
    content: str,
) -> tuple[str, str]:
    """Generate PDF using ReportLab with Unicode support"""
    ensure_upload_dir()
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    import markdown as md_lib

    agent_names = {"strategy": "战略规划", "brand": "品牌设计", "operations": "运营实施"}
    agent_name = agent_names.get(agent_type, agent_type)
    safe_brand = sanitize_filename(brand_name or "品牌")
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    file_name = f"{safe_brand}_{agent_name}_{timestamp}.pdf"
    file_path = os.path.join(UPLOAD_DIR, file_name)

    # Try to register Chinese font
    font_registered = False
    chinese_font_paths = [
        "/usr/share/fonts/wenquanyi/wqy-microhei/wqy-microhei.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/System/Library/Fonts/PingFang.ttc",
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
    ]
    font_name = "Helvetica"
    for fp in chinese_font_paths:
        if os.path.exists(fp):
            try:
                pdfmetrics.registerFont(TTFont("ChineseFont", fp))
                font_name = "ChineseFont"
                font_registered = True
                break
            except Exception:
                continue

    doc = SimpleDocTemplate(
        file_path,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CustomTitle",
        fontName=font_name,
        fontSize=20,
        textColor=colors.HexColor("#1a1a2e"),
        spaceAfter=12,
        leading=28,
    )
    h1_style = ParagraphStyle(
        "H1",
        fontName=font_name,
        fontSize=16,
        textColor=colors.HexColor("#16213e"),
        spaceBefore=16,
        spaceAfter=8,
        leading=22,
    )
    h2_style = ParagraphStyle(
        "H2",
        fontName=font_name,
        fontSize=13,
        textColor=colors.HexColor("#0f3460"),
        spaceBefore=12,
        spaceAfter=6,
        leading=18,
    )
    body_style = ParagraphStyle(
        "Body",
        fontName=font_name,
        fontSize=10,
        textColor=colors.HexColor("#333333"),
        spaceAfter=6,
        leading=16,
    )
    meta_style = ParagraphStyle(
        "Meta",
        fontName=font_name,
        fontSize=9,
        textColor=colors.HexColor("#888888"),
        spaceAfter=4,
    )

    story = []
    story.append(Paragraph(f"{brand_name or '品牌'} - {agent_name}方案", title_style))
    story.append(Paragraph(f"生成时间：{datetime.now().strftime('%Y年%m月%d日 %H:%M')}", meta_style))
    story.append(Paragraph("本方案由AI专家生成，仅供参考", meta_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e0e0e0"), spaceAfter=12))

    # Parse markdown lines to PDF
    lines = content.split("\n")
    for line in lines:
        line = line.strip()
        if not line:
            story.append(Spacer(1, 6))
            continue
        # Escape special chars for reportlab
        safe_line = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        if line.startswith("## "):
            story.append(Paragraph(safe_line[3:], h1_style))
        elif line.startswith("### "):
            story.append(Paragraph(safe_line[4:], h2_style))
        elif line.startswith("# "):
            story.append(Paragraph(safe_line[2:], title_style))
        elif line.startswith("- ") or line.startswith("* "):
            story.append(Paragraph(f"• {safe_line[2:]}", body_style))
        elif re.match(r'^\d+\.', line):
            story.append(Paragraph(safe_line, body_style))
        elif line.startswith("---"):
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc"), spaceAfter=6))
        elif line.startswith(">"):
            quote_style = ParagraphStyle("Quote", parent=body_style,
                                          leftIndent=20, textColor=colors.HexColor("#666666"),
                                          borderColor=colors.HexColor("#cccccc"),
                                          borderWidth=2, borderPadding=4)
            story.append(Paragraph(safe_line[1:].strip(), quote_style))
        else:
            story.append(Paragraph(safe_line, body_style))

    doc.build(story)
    return file_path, file_name


def generate_brand_png(
    task_id: int,
    brand_name: str,
    content: str,
) -> tuple[str, str]:
    """Generate brand style guide PNG using Pillow"""
    ensure_upload_dir()
    from PIL import Image, ImageDraw, ImageFont
    import re

    safe_brand = sanitize_filename(brand_name or "品牌")
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    file_name = f"{safe_brand}_品牌视觉_{timestamp}.png"
    file_path = os.path.join(UPLOAD_DIR, file_name)

    # Extract colors from content
    hex_colors = re.findall(r'#([A-Fa-f0-9]{6})', content)
    brand_colors = ["#" + c for c in hex_colors[:5]] if hex_colors else [
        "#1a1a2e", "#16213e", "#0f3460", "#e94560", "#f5f5f5"
    ]
    while len(brand_colors) < 5:
        brand_colors.append("#cccccc")

    W, H = 1920, 1080
    img = Image.new("RGB", (W, H), "#fafafa")
    draw = ImageDraw.Draw(img)

    # Background gradient-like header
    for y in range(180):
        r = int(26 + (y/180) * 10)
        g = int(26 + (y/180) * 5)
        b = int(46 + (y/180) * 20)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    # Try to load font
    font_large = ImageFont.load_default()
    font_medium = ImageFont.load_default()
    font_small = ImageFont.load_default()
    for fp in ["/usr/share/fonts/wenquanyi/wqy-microhei/wqy-microhei.ttc",
               "C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simhei.ttf"]:
        if os.path.exists(fp):
            try:
                font_large = ImageFont.truetype(fp, 64)
                font_medium = ImageFont.truetype(fp, 36)
                font_small = ImageFont.truetype(fp, 24)
                break
            except Exception:
                pass

    # Title
    draw.text((80, 50), brand_name or "品牌", font=font_large, fill="#ffffff")
    draw.text((80, 130), "Brand Visual Identity System", font=font_small, fill="#aaaacc")

    # Color palette section
    draw.rectangle([(0, 180), (W, 181)], fill="#e0e0e0")
    draw.text((80, 210), "品牌色彩系统", font=font_medium, fill="#1a1a2e")

    swatch_y = 270
    swatch_w = 300
    swatch_h = 200
    gap = 30
    for i, color in enumerate(brand_colors[:5]):
        x = 80 + i * (swatch_w + gap)
        # Color block
        draw.rectangle([(x, swatch_y), (x + swatch_w, swatch_y + swatch_h)], fill=color)
        # Hex label
        label_bg = "#ffffff" if _is_dark(color) else "#333333"
        label_color = "#333333" if _is_dark(color) else "#ffffff"
        draw.rectangle([(x, swatch_y + swatch_h), (x + swatch_w, swatch_y + swatch_h + 50)],
                        fill=label_bg)
        draw.text((x + 10, swatch_y + swatch_h + 10), color.upper(), font=font_small, fill=label_color)

    # Color name labels
    color_roles = ["主色调", "辅助色1", "辅助色2", "点缀色", "背景色"]
    for i, (color, role) in enumerate(zip(brand_colors[:5], color_roles)):
        x = 80 + i * (swatch_w + gap)
        draw.text((x + 10, swatch_y + swatch_h + 60), role, font=font_small, fill="#666666")

    # Logo area placeholder
    logo_x, logo_y = 80, 580
    draw.rectangle([(logo_x, logo_y), (logo_x + 400, logo_y + 300)],
                    outline="#cccccc", width=2, fill="#f0f0f0")
    draw.text((logo_x + 120, logo_y + 120), "LOGO", font=font_large, fill="#bbbbbb")
    draw.text((logo_x + 100, logo_y + 210), "设计概念区", font=font_small, fill="#aaaaaa")

    # Typography section
    type_x = 560
    draw.text((type_x, 580), "字体规范", font=font_medium, fill="#1a1a2e")
    draw.text((type_x, 640), brand_name or "品牌名称", font=font_large, fill="#1a1a2e")
    draw.text((type_x, 730), "Aa Bb Cc - 主标题字体", font=font_medium, fill="#333333")
    draw.text((type_x, 790), "品牌核心价值主张", font=font_small, fill="#666666")
    draw.text((type_x, 840), "Brand Core Value Proposition", font=font_small, fill="#999999")

    # Footer
    draw.rectangle([(0, H-60), (W, H)], fill="#1a1a2e")
    ts = datetime.now().strftime("%Y-%m-%d")
    draw.text((80, H-42), f"Generated by Blank_WEB · {ts} · AI Brand Strategy Platform",
               font=font_small, fill="#aaaacc")

    img.save(file_path, "PNG", quality=95)
    return file_path, file_name


def _is_dark(hex_color: str) -> bool:
    """Return True if color is dark (use white text on it)"""
    try:
        h = hex_color.lstrip("#")
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        return luminance < 0.5
    except Exception:
        return True
