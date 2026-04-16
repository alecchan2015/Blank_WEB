"""
Knowledge Base Document Upload & AI Extraction Service
Supports: PDF, DOCX, TXT, MD, ZIP (containing any of the above)
"""

import os
import json
import zipfile
import tempfile
from typing import List, Optional
from sqlalchemy.orm import Session


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}


async def process_uploaded_file(
    file_path: str,
    file_name: str,
    agent_type: str,
    db: Session,
    user_id: int,
) -> dict:
    """
    Main entry: process an uploaded file and extract knowledge entries.
    Returns {"success": bool, "entries_created": int, "error": str}
    """
    try:
        ext = os.path.splitext(file_name)[1].lower()

        if ext == ".zip":
            return await _process_zip(file_path, file_name, agent_type, db, user_id)

        if ext not in SUPPORTED_EXTENSIONS:
            return {"success": False, "entries_created": 0, "error": f"不支持的文件类型: {ext}"}

        text = _extract_text(file_path, ext)
        if not text or not text.strip():
            return {"success": False, "entries_created": 0, "error": "文件内容为空或无法提取文本"}

        chunks = chunk_text(text)
        total_created = 0
        for chunk in chunks:
            entries = await ai_extract_knowledge(chunk, agent_type, file_name, db)
            for entry in entries:
                _save_knowledge_entry(entry, agent_type, file_name, db, user_id)
                total_created += 1

        return {"success": True, "entries_created": total_created, "error": ""}
    except Exception as e:
        return {"success": False, "entries_created": 0, "error": str(e)}


async def _process_zip(
    zip_path: str,
    zip_name: str,
    agent_type: str,
    db: Session,
    user_id: int,
) -> dict:
    """Extract files from ZIP and process each one."""
    total_created = 0
    errors = []
    with tempfile.TemporaryDirectory() as tmp_dir:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(tmp_dir)
            for name in zf.namelist():
                ext = os.path.splitext(name)[1].lower()
                if ext not in SUPPORTED_EXTENSIONS:
                    continue
                extracted_path = os.path.join(tmp_dir, name)
                if not os.path.isfile(extracted_path):
                    continue
                result = await process_uploaded_file(
                    extracted_path,
                    os.path.basename(name),
                    agent_type,
                    db,
                    user_id,
                )
                total_created += result.get("entries_created", 0)
                if result.get("error"):
                    errors.append(f"{name}: {result['error']}")

    return {
        "success": total_created > 0 or not errors,
        "entries_created": total_created,
        "error": "; ".join(errors) if errors else "",
    }


def _extract_text(file_path: str, ext: str) -> str:
    """Route to the correct text extraction function."""
    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext == ".docx":
        return extract_text_from_docx(file_path)
    elif ext in (".txt", ".md"):
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    return ""


def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF, trying pdfplumber first, fallback to PyPDF2."""
    try:
        import pdfplumber
        text_parts = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        if text_parts:
            return "\n\n".join(text_parts)
    except ImportError:
        pass
    except Exception:
        pass

    # Fallback to PyPDF2
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(file_path)
        text_parts = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        return "\n\n".join(text_parts)
    except ImportError:
        raise RuntimeError("需要安装 pdfplumber 或 PyPDF2 来处理 PDF 文件")
    except Exception as e:
        raise RuntimeError(f"PDF 解析失败: {e}")


def extract_text_from_docx(file_path: str) -> str:
    """Extract text from DOCX using python-docx."""
    try:
        from docx import Document
        doc = Document(file_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n\n".join(paragraphs)
    except ImportError:
        raise RuntimeError("需要安装 python-docx 来处理 DOCX 文件")
    except Exception as e:
        raise RuntimeError(f"DOCX 解析失败: {e}")


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list:
    """Split text into chunks with overlap."""
    if not text:
        return []
    text = text.strip()
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk.strip())
        start += chunk_size - overlap

    return chunks


async def ai_extract_knowledge(
    text_chunk: str,
    agent_type: str,
    source_file: str,
    db: Session,
) -> list:
    """
    Use LLM to extract knowledge entries from a text chunk.
    Returns list of dicts: [{title, content, knowledge_type, tags}]
    """
    from services.llm_service import LLMService, get_llm_config_for_agent

    # Find an active LLM config for extraction
    config = get_llm_config_for_agent("all", db)
    if not config:
        config = get_llm_config_for_agent("strategy", db)
    if not config:
        # Fallback: just create a single entry from the chunk directly
        return _fallback_extract(text_chunk, source_file)

    agent_label = {
        "strategy": "战略规划",
        "brand": "品牌设计",
        "operations": "运营实施",
    }.get(agent_type, agent_type)

    prompt = f"""你是一个知识库提取助手。请分析以下文本，提取对"{agent_label}"领域有价值的知识条目。

文本来源文件: {source_file}

文本内容:
---
{text_chunk}
---

请提取知识条目，以JSON数组格式返回。每个条目包含:
- title: 简洁的标题（不超过100字）
- content: 知识内容摘要（200-500字，保留关键信息）
- knowledge_type: 类型，从以下选择: framework, case_study, market_data, methodology, industry_report, general
- tags: 标签，逗号分隔（3-5个标签）

如果文本没有对"{agent_label}"领域有价值的知识，返回空数组 []。

只返回JSON数组，不要其他内容。示例格式:
[{{"title": "...", "content": "...", "knowledge_type": "methodology", "tags": "标签1,标签2"}}]"""

    messages = [
        {"role": "system", "content": "你是知识提取助手，只返回合法的JSON数组。"},
        {"role": "user", "content": prompt},
    ]

    try:
        llm = LLMService()
        response = await llm.complete(
            messages=messages,
            provider=config.provider,
            api_key=config.api_key,
            model_name=config.model_name,
            base_url=config.base_url,
            db=db,
            agent_type="knowledge_extract",
        )

        # Parse JSON from response
        response = response.strip()
        # Handle markdown code blocks
        if response.startswith("```"):
            lines = response.split("\n")
            response = "\n".join(lines[1:-1])

        entries = json.loads(response)
        if not isinstance(entries, list):
            entries = [entries]

        # Validate entries
        valid = []
        for e in entries:
            if isinstance(e, dict) and e.get("title") and e.get("content"):
                valid.append({
                    "title": str(e["title"])[:200],
                    "content": str(e["content"]),
                    "knowledge_type": str(e.get("knowledge_type", "general"))[:50],
                    "tags": str(e.get("tags", ""))[:500],
                })
        return valid

    except Exception as e:
        print(f"[KBUpload] AI extraction failed: {e}")
        return _fallback_extract(text_chunk, source_file)


def _fallback_extract(text_chunk: str, source_file: str) -> list:
    """Simple fallback when LLM is unavailable."""
    title = source_file
    if len(text_chunk) > 60:
        title = text_chunk[:60].replace("\n", " ").strip() + "..."
    return [{
        "title": title,
        "content": text_chunk[:2000],
        "knowledge_type": "general",
        "tags": os.path.splitext(source_file)[0],
    }]


def _save_knowledge_entry(
    entry: dict,
    agent_type: str,
    source_file: str,
    db: Session,
    user_id: int,
):
    """Persist a single knowledge entry to the database."""
    from models import AgentKnowledge

    item = AgentKnowledge(
        agent_type=agent_type,
        title=entry["title"],
        content=entry["content"],
        created_by=user_id,
        knowledge_type=entry.get("knowledge_type", "general"),
        source="upload",
        source_file=source_file,
        quality_score=7,
        tags=entry.get("tags", ""),
    )
    db.add(item)
    db.commit()


def import_seed_knowledge(db: Session, user_id: int) -> int:
    """
    Import built-in seed knowledge entries.
    Returns count of entries created.
    """
    from models import AgentKnowledge

    # Check if seed data already exists
    existing = db.query(AgentKnowledge).filter(
        AgentKnowledge.source == "seed"
    ).count()
    if existing > 0:
        return 0  # Already imported

    seeds = _get_seed_entries()
    count = 0
    for entry in seeds:
        item = AgentKnowledge(
            agent_type=entry["agent_type"],
            title=entry["title"],
            content=entry["content"],
            created_by=user_id,
            knowledge_type=entry.get("knowledge_type", "general"),
            source="seed",
            source_file=None,
            quality_score=entry.get("quality_score", 8),
            tags=entry.get("tags", ""),
        )
        db.add(item)
        count += 1
    db.commit()
    return count


def _get_seed_entries() -> list:
    """Built-in seed knowledge for each agent type."""
    return [
        {
            "agent_type": "strategy",
            "title": "SWOT分析框架",
            "content": "SWOT分析是战略规划中最常用的分析工具之一。S(Strengths)优势：组织内部的有利因素；W(Weaknesses)劣势：组织内部的不利因素；O(Opportunities)机会：外部环境中的有利因素；T(Threats)威胁：外部环境中的不利因素。使用时应结合行业特点，将四个维度交叉分析，形成SO、WO、ST、WT四种策略组合。",
            "knowledge_type": "framework",
            "quality_score": 9,
            "tags": "战略分析,SWOT,分析框架,竞争策略",
        },
        {
            "agent_type": "strategy",
            "title": "波特五力模型",
            "content": "波特五力模型用于分析行业竞争格局：1)现有竞争者的竞争强度；2)潜在进入者的威胁；3)替代品的威胁；4)供应商的议价能力；5)购买者的议价能力。通过五力分析，可以判断行业吸引力和利润潜力，为企业制定竞争战略提供依据。",
            "knowledge_type": "framework",
            "quality_score": 9,
            "tags": "波特五力,竞争分析,行业分析,战略框架",
        },
        {
            "agent_type": "strategy",
            "title": "蓝海战略方法论",
            "content": "蓝海战略的核心是创造无人竞争的新市场空间。关键工具包括：战略画布（对比行业竞争要素）、四步行动框架（剔除-减少-增加-创造）、以及价值创新（同时追求差异化和低成本）。成功案例包括太阳马戏团、任天堂Wii等。",
            "knowledge_type": "methodology",
            "quality_score": 8,
            "tags": "蓝海战略,价值创新,战略画布,差异化",
        },
        {
            "agent_type": "brand",
            "title": "品牌定位黄金三角",
            "content": "品牌定位需要考虑三个核心维度：1)目标消费者需求与痛点；2)品牌自身的核心优势与资源；3)竞品的定位空白区域。三者交叉处即为最佳定位点。定位需要用一句话清晰表达，如'怕上火，喝王老吉'。",
            "knowledge_type": "framework",
            "quality_score": 9,
            "tags": "品牌定位,消费者洞察,竞争分析,定位策略",
        },
        {
            "agent_type": "brand",
            "title": "品牌视觉识别系统(VIS)要素",
            "content": "完整的品牌VIS包括：基础系统（标志、标准色、标准字、辅助图形）和应用系统（名片、信纸、包装、店面、车体广告等）。设计原则：简洁易识别、适用性强、具有延展性、符合品牌调性。色彩心理学在品牌设计中至关重要。",
            "knowledge_type": "methodology",
            "quality_score": 8,
            "tags": "VIS,视觉识别,品牌设计,色彩心理学",
        },
        {
            "agent_type": "brand",
            "title": "品牌故事构建方法",
            "content": "优秀的品牌故事包含四个要素：1)起源故事（创始人/品牌诞生的初心）；2)核心冲突（解决什么问题）；3)价值主张（独特的解决方案）；4)情感连接（与消费者共鸣的情感）。故事要真实、有温度、能引发共鸣。",
            "knowledge_type": "methodology",
            "quality_score": 8,
            "tags": "品牌故事,情感营销,品牌叙事,消费者共鸣",
        },
        {
            "agent_type": "operations",
            "title": "数字营销漏斗优化",
            "content": "AARRR海盗模型是数字运营的核心框架：Acquisition(获取)、Activation(激活)、Retention(留存)、Revenue(变现)、Referral(推荐)。每个环节需要设定关键指标(KPI)并持续优化。重点关注CAC(获客成本)和LTV(用户终生价值)的比值。",
            "knowledge_type": "framework",
            "quality_score": 9,
            "tags": "AARRR,数字营销,增长黑客,用户运营",
        },
        {
            "agent_type": "operations",
            "title": "内容运营方法论",
            "content": "内容运营的核心闭环：策划(选题+定位) -> 生产(原创+UGC) -> 分发(渠道匹配) -> 数据(效果跟踪) -> 迭代(优化调整)。内容选题要结合热点、痛点、卖点。不同平台需要差异化内容策略，如小红书偏种草、抖音偏娱乐、微信偏深度。",
            "knowledge_type": "methodology",
            "quality_score": 8,
            "tags": "内容运营,选题策划,渠道分发,数据驱动",
        },
        {
            "agent_type": "operations",
            "title": "社群运营SOP",
            "content": "社群运营标准流程：1)社群定位与目标人群画像；2)入群门槛设计（付费/审核/邀请）；3)内容规划（日常/活动/福利）；4)活跃度维护（话题/打卡/互动）；5)转化设计（种草-体验-转化-复购）；6)数据追踪（活跃率/转化率/退群率）。",
            "knowledge_type": "methodology",
            "quality_score": 8,
            "tags": "社群运营,SOP,用户活跃,转化率",
        },
    ]
