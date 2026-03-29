from app.services.bootstrap_service import bootstrap_application
from app.db.session import get_connection
from app.services.orchestration_service import OrchestrationService


def main() -> None:
    bootstrap_application()
    with get_connection() as connection:
        OrchestrationService(connection).run_pipeline_for_active_sources()


if __name__ == "__main__":
    main()
