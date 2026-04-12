import os
import json
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from fastapi import FastAPI, Depends, HTTPException, status, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse

from database import Base, engine, get_db
from models import User, LLMConfig, AgentKnowledge, Task, TaskResult, CreditTransaction
from auth import (
    get_password_hash, verify_password, create_access_token,
    get_current_user, get_current_admin
)
from schemas import (
    UserRegister, UserLogin, UserOut, TokenResponse,
    LLMConfigCreate, LLMConfigOut,
    KnowledgeCreate, KnowledgeOut,
    TaskCreate, TaskOut, TaskResultOut,
    UserCreditsUpdate, UserStatusUpdate,
)
from services.agent_service import run_multi_agent, AGENT_META
from services.file_service import generate_markdown_file, generate_pdf_file, generate_brand_png

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Init DB
    Base.metadata.create_all(bind=engine)
    Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    # Seed default admin
    db = next(get_db())
    try:
        if not db.query(User).filter(User.username == "admin").first():
            admin = User(
                username="admin",
                email="admin@blankweb.com",
                password_hash=get_password_hash("Admin@123"),
                role="admin",
                credits=99999,
            )
            db.add(admin)
            db.commit()
    finally:
        db.close()
    yield


app = FastAPI(
    title="Blank_WEB - 家具品牌战略AI平台",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────
# Auth Routes
# ─────────────────────────────────────────────

@app.post("/api/auth/register", response_model=UserOut, tags=["auth"])
def register(body: UserRegister, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == body.username).first():
        raise HTTPException(400, "用户名已存在")
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(400, "邮箱已被注册")
    user = User(
        username=body.username,
        email=body.email,
        password_hash=get_password_hash(body.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/api/auth/login", response_model=TokenResponse, tags=["auth"])
def login(body: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == body.username).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "用户名或密码错误")
    if not user.is_active:
        raise HTTPException(403, "账号已被禁用")
    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer", "user": user}


@app.get("/api/auth/me", response_model=UserOut, tags=["auth"])
def me(current_user: User = Depends(get_current_user)):
    return current_user


# ─────────────────────────────────────────────
# Task Routes
# ─────────────────────────────────────────────

@app.post("/api/tasks", response_model=TaskOut, tags=["tasks"])
def create_task(
    body: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    valid_agents = {"strategy", "brand", "operations"}
    agents = [a for a in body.agents_selected if a in valid_agents]
    if not agents:
        raise HTTPException(400, "请至少选择一个Agent专家")
    task = Task(
        user_id=current_user.id,
        query=body.query,
        agents_selected=agents,
        brand_name=body.brand_name,
        status="pending",
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@app.get("/api/tasks", response_model=List[TaskOut], tags=["tasks"])
def list_tasks(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tasks = (
        db.query(Task)
        .filter(Task.user_id == current_user.id)
        .order_by(Task.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return tasks


@app.get("/api/tasks/{task_id}", response_model=TaskOut, tags=["tasks"])
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(404, "任务不存在")
    if task.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(403, "无权访问")
    return task


@app.get("/api/tasks/{task_id}/stream", tags=["tasks"])
async def stream_task(
    task_id: int,
    token: str = Query(...),
    db: Session = Depends(get_db),
):
    """SSE endpoint for streaming task processing"""
    from jose import jwt, JWTError
    from auth import SECRET_KEY, ALGORITHM

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(401, "Unauthorized")
    except JWTError:
        raise HTTPException(401, "Invalid token")

    task = db.query(Task).filter(Task.id == task_id).first()
    if not task or task.user_id != user.id:
        raise HTTPException(404, "Task not found")

    if task.status in ("completed", "failed"):
        async def replay():
            yield {"data": json.dumps({"type": "already_done", "status": task.status})}
        return EventSourceResponse(replay())

    async def event_generator():
        agent_contents = {}
        task.status = "processing"
        db.commit()

        try:
            async for event in run_multi_agent(
                agents=task.agents_selected,
                query=task.query,
                brand_name=task.brand_name or "",
                db=db,
            ):
                etype = event.get("type")
                if etype == "agent_start":
                    yield {"data": json.dumps(event)}

                elif etype == "chunk":
                    yield {"data": json.dumps({
                        "type": "chunk",
                        "agent": event["agent"],
                        "content": event["content"],
                    })}

                elif etype == "agent_done":
                    agent_type = event["agent"]
                    full_content = event["full_content"]
                    agent_contents[agent_type] = full_content

                    # Save TaskResult
                    tr = TaskResult(
                        task_id=task.id,
                        agent_type=agent_type,
                        content=full_content,
                        download_credits=10,
                    )
                    db.add(tr)
                    db.commit()
                    db.refresh(tr)

                    # Generate files
                    files_generated = []
                    try:
                        md_path, md_name = generate_markdown_file(
                            task.id, agent_type, task.brand_name or "品牌", full_content
                        )
                        md_result = TaskResult(
                            task_id=task.id,
                            agent_type=agent_type,
                            content=None,
                            file_path=md_path,
                            file_type="md",
                            file_name=md_name,
                            download_credits=5,
                        )
                        db.add(md_result)
                        db.commit()
                        db.refresh(md_result)
                        files_generated.append({"id": md_result.id, "type": "md", "name": md_name})
                    except Exception as e:
                        print(f"MD gen error: {e}")

                    try:
                        pdf_path, pdf_name = generate_pdf_file(
                            task.id, agent_type, task.brand_name or "品牌", full_content
                        )
                        pdf_result = TaskResult(
                            task_id=task.id,
                            agent_type=agent_type,
                            content=None,
                            file_path=pdf_path,
                            file_type="pdf",
                            file_name=pdf_name,
                            download_credits=10,
                        )
                        db.add(pdf_result)
                        db.commit()
                        db.refresh(pdf_result)
                        files_generated.append({"id": pdf_result.id, "type": "pdf", "name": pdf_name})
                    except Exception as e:
                        print(f"PDF gen error: {e}")

                    if agent_type == "brand":
                        try:
                            png_path, png_name = generate_brand_png(
                                task.id, task.brand_name or "品牌", full_content
                            )
                            png_result = TaskResult(
                                task_id=task.id,
                                agent_type=agent_type,
                                content=None,
                                file_path=png_path,
                                file_type="png",
                                file_name=png_name,
                                download_credits=15,
                            )
                            db.add(png_result)
                            db.commit()
                            db.refresh(png_result)
                            files_generated.append({"id": png_result.id, "type": "png", "name": png_name})
                        except Exception as e:
                            print(f"PNG gen error: {e}")

                    yield {"data": json.dumps({
                        "type": "agent_done",
                        "agent": agent_type,
                        "result_id": tr.id,
                        "files": files_generated,
                    })}

            task.status = "completed"
            task.completed_at = datetime.utcnow()
            db.commit()
            yield {"data": json.dumps({"type": "all_done"})}

        except Exception as e:
            task.status = "failed"
            db.commit()
            yield {"data": json.dumps({"type": "error", "message": str(e)})}

    return EventSourceResponse(event_generator())


@app.delete("/api/tasks/{task_id}", tags=["tasks"])
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(404, "任务不存在")
    if task.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(403, "无权删除")
    db.delete(task)
    db.commit()
    return {"message": "已删除"}


# ─────────────────────────────────────────────
# File Download Routes
# ─────────────────────────────────────────────

@app.get("/api/files/{result_id}/download", tags=["files"])
def download_file(
    result_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = db.query(TaskResult).filter(TaskResult.id == result_id).first()
    if not result:
        raise HTTPException(404, "文件不存在")

    task = db.query(Task).filter(Task.id == result.task_id).first()
    if task.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(403, "无权下载")

    if not result.file_path:
        raise HTTPException(400, "此记录无文件")

    credits_needed = result.download_credits
    if current_user.credits < credits_needed:
        raise HTTPException(402, f"积分不足，需要 {credits_needed} 积分，当前 {current_user.credits} 积分")

    # Deduct credits
    current_user.credits -= credits_needed
    tx = CreditTransaction(
        user_id=current_user.id,
        amount=-credits_needed,
        reason=f"下载文件 {result.file_name}",
        task_result_id=result.id,
    )
    db.add(tx)
    db.commit()

    media_types = {
        "md": "text/markdown",
        "pdf": "application/pdf",
        "png": "image/png",
    }
    media_type = media_types.get(result.file_type, "application/octet-stream")
    return FileResponse(
        path=result.file_path,
        filename=result.file_name,
        media_type=media_type,
    )


@app.get("/api/files/{result_id}/preview", tags=["files"])
def preview_file(
    result_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Preview MD content without credits"""
    result = db.query(TaskResult).filter(TaskResult.id == result_id).first()
    if not result:
        raise HTTPException(404, "文件不存在")
    task = db.query(Task).filter(Task.id == result.task_id).first()
    if task.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(403, "无权预览")
    return {"content": result.content, "file_type": result.file_type}


# ─────────────────────────────────────────────
# Admin Routes
# ─────────────────────────────────────────────

@app.get("/api/admin/stats", tags=["admin"])
def admin_stats(db: Session = Depends(get_db), _=Depends(get_current_admin)):
    return {
        "total_users": db.query(User).filter(User.role == "user").count(),
        "total_tasks": db.query(Task).count(),
        "completed_tasks": db.query(Task).filter(Task.status == "completed").count(),
        "total_llm_configs": db.query(LLMConfig).filter(LLMConfig.is_active == True).count(),
        "total_knowledge": db.query(AgentKnowledge).filter(AgentKnowledge.is_active == True).count(),
    }


# LLM Config
@app.post("/api/admin/llm-configs", response_model=LLMConfigOut, tags=["admin"])
def create_llm_config(
    body: LLMConfigCreate,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    config = LLMConfig(**body.model_dump())
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


@app.get("/api/admin/llm-configs", response_model=List[LLMConfigOut], tags=["admin"])
def list_llm_configs(db: Session = Depends(get_db), _=Depends(get_current_admin)):
    return db.query(LLMConfig).order_by(LLMConfig.created_at.desc()).all()


@app.put("/api/admin/llm-configs/{config_id}", response_model=LLMConfigOut, tags=["admin"])
def update_llm_config(
    config_id: int,
    body: LLMConfigCreate,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    config = db.query(LLMConfig).filter(LLMConfig.id == config_id).first()
    if not config:
        raise HTTPException(404, "配置不存在")
    for k, v in body.model_dump().items():
        setattr(config, k, v)
    db.commit()
    db.refresh(config)
    return config


@app.delete("/api/admin/llm-configs/{config_id}", tags=["admin"])
def delete_llm_config(
    config_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    config = db.query(LLMConfig).filter(LLMConfig.id == config_id).first()
    if not config:
        raise HTTPException(404, "配置不存在")
    db.delete(config)
    db.commit()
    return {"message": "已删除"}


# Knowledge Base
@app.post("/api/admin/knowledge", response_model=KnowledgeOut, tags=["admin"])
def create_knowledge(
    body: KnowledgeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    item = AgentKnowledge(**body.model_dump(), created_by=current_user.id)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.get("/api/admin/knowledge", response_model=List[KnowledgeOut], tags=["admin"])
def list_knowledge(
    agent_type: Optional[str] = None,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    q = db.query(AgentKnowledge)
    if agent_type:
        q = q.filter(AgentKnowledge.agent_type == agent_type)
    return q.order_by(AgentKnowledge.created_at.desc()).all()


@app.put("/api/admin/knowledge/{item_id}", response_model=KnowledgeOut, tags=["admin"])
def update_knowledge(
    item_id: int,
    body: KnowledgeCreate,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    item = db.query(AgentKnowledge).filter(AgentKnowledge.id == item_id).first()
    if not item:
        raise HTTPException(404, "知识条目不存在")
    for k, v in body.model_dump().items():
        setattr(item, k, v)
    db.commit()
    db.refresh(item)
    return item


@app.delete("/api/admin/knowledge/{item_id}", tags=["admin"])
def delete_knowledge(
    item_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    item = db.query(AgentKnowledge).filter(AgentKnowledge.id == item_id).first()
    if not item:
        raise HTTPException(404, "知识条目不存在")
    db.delete(item)
    db.commit()
    return {"message": "已删除"}


# User Management
@app.get("/api/admin/users", response_model=List[UserOut], tags=["admin"])
def list_users(db: Session = Depends(get_db), _=Depends(get_current_admin)):
    return db.query(User).order_by(User.created_at.desc()).all()


@app.put("/api/admin/users/{user_id}/credits", response_model=UserOut, tags=["admin"])
def update_user_credits(
    user_id: int,
    body: UserCreditsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "用户不存在")
    delta = body.credits - user.credits
    user.credits = body.credits
    tx = CreditTransaction(
        user_id=user.id,
        amount=delta,
        reason=body.reason or "管理员调整",
    )
    db.add(tx)
    db.commit()
    db.refresh(user)
    return user


@app.put("/api/admin/users/{user_id}/status", response_model=UserOut, tags=["admin"])
def update_user_status(
    user_id: int,
    body: UserStatusUpdate,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "用户不存在")
    user.is_active = body.is_active
    db.commit()
    db.refresh(user)
    return user


@app.get("/api/admin/tasks", response_model=List[TaskOut], tags=["admin"])
def admin_list_tasks(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    return (
        db.query(Task)
        .order_by(Task.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


# ─────────────────────────────────────────────
# Agent Meta Info
# ─────────────────────────────────────────────
@app.get("/api/agents", tags=["agents"])
def get_agents():
    return [
        {"type": k, "name": v["name"], "icon": v["icon"]}
        for k, v in AGENT_META.items()
    ]


# Serve frontend in production
frontend_dist = Path("../frontend/dist")
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
