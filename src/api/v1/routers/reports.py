from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from src.domain.services.report_service import ReportService
from src.api.v1.schemas.report import DownloadUrlResponse, ReportResponse
from src.api.v1.dependencies import get_report_service
from src.storage.minio_service import minio_service


reports_router = APIRouter(prefix='/api/v1/reports', tags=['reports'])

@reports_router.get(
    '/{report_id}',
    response_model=ReportResponse,
)
async def get_report(report_id: int, service: ReportService = Depends(get_report_service)):
    try:
        return await service.get_report(report_id)
    
    except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

@reports_router.get("/{report_id}/download")
async def download_report(
    report_id: int,
    service: ReportService = Depends(get_report_service)
):
    report = await service.get_report(report_id)

    if report.status != "completed":
        raise HTTPException(
            status_code=400,
            detail="Report is not ready"
        )

    obj = minio_service.client.get_object(
        bucket_name="reports",
        object_name=report.file_path
    )

    return StreamingResponse(
        obj,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition":
                f'attachment; filename="{report.file_name}"'
        }
    )