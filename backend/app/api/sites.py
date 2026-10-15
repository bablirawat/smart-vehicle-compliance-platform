from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.sites import Site
from app.models.users import User, UserRole
from app.auth.rbac import get_current_user

router = APIRouter(prefix="/sites", tags=["Sites"])

@router.get("")
def list_sites(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = db.query(Site)
    # If site specific role like Operator or Site Manager, filter to their site unless Regional/Admin
    if current_user.role in [UserRole.OPERATOR, UserRole.SITE_MANAGER] and current_user.site_id:
        query = query.filter(Site.id == current_user.site_id)
    sites = query.all()
    return [{
        "id": s.id,
        "name": s.name,
        "code": s.code,
        "location": s.location,
        "status": s.status.value,
        "max_queue_capacity": s.max_queue_capacity
    } for s in sites]

@router.get("/{site_id}")
def get_site(site_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail=f"Site #{site_id} not found.")
    return {
        "id": site.id,
        "name": site.name,
        "code": site.code,
        "location": site.location,
        "status": site.status.value,
        "max_queue_capacity": site.max_queue_capacity,
        "cameras": [{"id": c.id, "code": c.camera_code, "type": c.type.value, "status": c.status.value} for c in site.cameras],
        "bays": [{"id": b.id, "name": b.bay_name, "type": b.bay_type, "status": b.status.value} for b in site.bays]
    }
