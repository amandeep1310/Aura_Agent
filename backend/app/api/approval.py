from fastapi import APIRouter

router = APIRouter()

# Approval route handlers
# POST /approval/{poster_id}/approve
# POST /approval/{poster_id}/reject
# POST /approval/{poster_id}/request-change
