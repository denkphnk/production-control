from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from src.data.models.report import Report
from src.data.repositories.batch_repository import BatchRepository
from src.data.repositories.report_repository import ReportRepository
from src.storage.minio_service import minio_service

class ReportService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.report_repo = ReportRepository(session)
        self.batch_repo = BatchRepository(session)

    async def create_report(self, batch_id: int) -> Report:
        batch = await self.batch_repo.get_by_id(batch_id)

        if not batch:
            raise ValueError(f'Batch with ID {batch_id} not found')
        
        report = await self.report_repo.create(
            {
                "batch_id": batch_id,
                "status": "pending",
                "file_name": "",
                "file_path": ""
            }
        )

        await self.session.commit()
        # TODO: generate_report
        # generate_report.delay(report.id)

        return report

    async def get_report(self, report_id: int) -> Report:
        report = await self.report_repo.get_by_id(report_id)
        if not report:
            raise ValueError(f'Report with ID {report_id} not found')

        return report

    async def get_reports_by_batch(self, batch_id: int) -> List[Report]:
        batch = await self.batch_repo.get_by_id(batch_id)
        if not batch:
            raise ValueError(f'Batch with ID {batch_id} not found')

        reports = await self.report_repo.get_by_batch_id(batch_id)
        return reports

    async def get_download_url(self, report_id: int) -> str:
        report = await self.report_repo.get_by_id(report_id)
        if not report:
            raise ValueError(f'Report with ID {report_id} not found')

        if report.status != "completed":
            raise ValueError("Report is not ready")

        url = minio_service.get_presigned_url(
            bucket_name='reports',
            object_name=report.file_path
        )

        return url