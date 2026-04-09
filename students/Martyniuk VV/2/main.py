from fastapi import FastAPI
from infrastructure.adapters.repositories.in_memory_idea_repository import InMemoryIdeaRepository
from infrastructure.adapters.services.mock_moderation_service import MockModerationService
from application.use_cases.idea_use_cases import IdeaUseCases
from infrastructure.api.rest_controller import setup_routes


def create_app() -> FastAPI:
    """Фабрика приложения — собираем все зависимости"""

    # 1. Создаем адаптеры (инфраструктура)
    repository = InMemoryIdeaRepository()
    moderation_service = MockModerationService()


    idea_service = IdeaUseCases(
        idea_repository=repository,
        moderation_service=moderation_service
    )

    # 3. Создаем FastAPI и подключаем роуты
    app = FastAPI(title="Idea Service", version="1.0.0")
    setup_routes(app, idea_service)

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
