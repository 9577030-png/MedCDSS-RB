from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from application.services.version_manager import VersionManager
from domain.interfaces import RuleRepository
from domain.rule_version import RuleVersion
from domain.exceptions import VersionNotFoundError

router = APIRouter(prefix="/admin/rules", tags=["admin"])

class ReloadResponse(BaseModel):
    loaded: int
    versions: List[dict]

class ActivateRequest(BaseModel):
    rule_id: str
    version_id: int

def get_version_manager(rule_repo: RuleRepository, config_dir: str) -> VersionManager:
    # Здесь нужно получить экземпляр из глобальной зависимости
    # Для простоты передаём через глобальную переменную или через фабрику
    pass

@router.post("/reload")
async def reload_rules(version_manager: VersionManager = Depends(get_version_manager)):
    """Перезагрузить все правила из YAML (создать новые версии)."""
    new_versions = version_manager.hot_reload(created_by="admin")
    return ReloadResponse(
        loaded=len(new_versions),
        versions=[{"rule_id": v.rule_id, "version_id": v.version_id, "is_active": v.is_active} for v in new_versions]
    )

@router.put("/activate")
async def activate_version(req: ActivateRequest, version_manager: VersionManager = Depends(get_version_manager)):
    """Активировать указанную версию правила."""
    try:
        version_manager.activate_version(req.rule_id, req.version_id)
    except VersionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"status": "ok", "rule_id": req.rule_id, "version_id": req.version_id}

@router.get("/history/{rule_id}")
async def get_history(rule_id: str, version_manager: VersionManager = Depends(get_version_manager)):
    """Получить историю версий правила."""
    history = version_manager.get_history(rule_id)
    if not history:
        raise HTTPException(status_code=404, detail="Rule not found")
    return [{"version_id": v.version_id, "created_at": v.created_at, "is_active": v.is_active, "comment": v.comment} for v in history]