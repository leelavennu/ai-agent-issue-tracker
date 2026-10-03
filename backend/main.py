from datetime import datetime, timezone
from enum import Enum
from typing import Generator

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import DateTime, Integer, String, Text, create_engine, func, or_, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

DATABASE_URL = "sqlite:///./issues.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class Base(DeclarativeBase):
    pass

class Issue(Base):
    __tablename__ = "issues"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="open", index=True)
    priority: Mapped[str] = mapped_column(String(20), default="medium", index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

Base.metadata.create_all(bind=engine)

class IssueStatus(str, Enum):
    open = "open"
    closed = "closed"

class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"

class IssueBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=5000)
    status: IssueStatus = IssueStatus.open
    priority: Priority = Priority.medium

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Title cannot be empty")
        return value

class IssueCreate(IssueBase):
    pass

class IssueUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    status: IssueStatus | None = None
    priority: Priority | None = None
    version: int | None = Field(default=None, ge=1)

    @field_validator("title")
    @classmethod
    def update_title_not_blank(cls, value: str | None) -> str | None:
        if value is not None:
            value = value.strip()
            if not value:
                raise ValueError("Title cannot be empty")
        return value

class IssueRead(IssueBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    version: int
    created_at: datetime
    updated_at: datetime

class IssueList(BaseModel):
    items: list[IssueRead]
    total: int
    page: int
    limit: int
    pages: int

app = FastAPI(title="AI-Agent-Ready Issue Tracker API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_role(x_user_role: str | None = Header(default=None)) -> str | None:
    if x_user_role not in (None, "admin", "user"):
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    return x_user_role


def issue_or_404(db: Session, issue_id: int) -> Issue:
    issue = db.get(Issue, issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    return issue

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

@app.get("/issues", response_model=IssueList)
def list_issues(
    status_filter: IssueStatus | None = Query(default=None, alias="status"),
    priority: Priority | None = None,
    search: str | None = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    sort: str = Query(default="updated_at"),
    order: str = Query(default="desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
) -> IssueList:
    query = select(Issue)
    count_query = select(func.count()).select_from(Issue)
    filters = []
    if status_filter: filters.append(Issue.status == status_filter.value)
    if priority: filters.append(Issue.priority == priority.value)
    if search:
        term = f"%{search}%"
        filters.append(or_(Issue.title.ilike(term), Issue.description.ilike(term)))
    if filters:
        query = query.where(*filters)
        count_query = count_query.where(*filters)
    sort_column = {"id": Issue.id, "title": Issue.title, "priority": Issue.priority, "status": Issue.status, "created_at": Issue.created_at, "updated_at": Issue.updated_at}.get(sort, Issue.updated_at)
    query = query.order_by(sort_column.asc() if order == "asc" else sort_column.desc()).offset((page - 1) * limit).limit(limit)
    items = list(db.scalars(query))
    total = db.scalar(count_query) or 0
    return IssueList(items=items, total=total, page=page, limit=limit, pages=(total + limit - 1) // limit)

@app.post("/issues", response_model=IssueRead, status_code=status.HTTP_201_CREATED)
def create_issue(payload: IssueCreate, db: Session = Depends(get_db)) -> Issue:
    if db.scalar(select(Issue).where(Issue.title == payload.title)):
        raise HTTPException(status_code=409, detail="An issue with this title already exists")
    issue = Issue(**payload.model_dump())
    issue.status = issue.status.value if isinstance(issue.status, IssueStatus) else issue.status
    issue.priority = issue.priority.value if isinstance(issue.priority, Priority) else issue.priority
    db.add(issue)
    db.commit()
    db.refresh(issue)
    return issue

@app.get("/issues/{issue_id}", response_model=IssueRead)
def get_issue(issue_id: int, db: Session = Depends(get_db)) -> Issue:
    return issue_or_404(db, issue_id)

@app.put("/issues/{issue_id}", response_model=IssueRead)
def update_issue(issue_id: int, payload: IssueUpdate, db: Session = Depends(get_db), role: str | None = Depends(get_role)) -> Issue:
    issue = issue_or_404(db, issue_id)
    data = payload.model_dump(exclude_unset=True)
    expected_version = data.pop("version", None)
    if expected_version is not None and expected_version != issue.version:
        raise HTTPException(status_code=409, detail="Issue changed since it was loaded; refresh and try again")
    new_title = data.get("title")
    if new_title and new_title != issue.title and db.scalar(select(Issue).where(Issue.title == new_title)):
        raise HTTPException(status_code=409, detail="An issue with this title already exists")
    for key, value in data.items():
        setattr(issue, key, value.value if isinstance(value, (IssueStatus, Priority)) else value)
    issue.version += 1
    issue.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(issue)
    return issue

@app.delete("/issues/{issue_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_issue(issue_id: int, db: Session = Depends(get_db), role: str | None = Depends(get_role)) -> None:
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required to delete issues")
    issue = issue_or_404(db, issue_id)
    db.delete(issue)
    db.commit()
