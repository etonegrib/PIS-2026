import uuid
from typing import List, Optional
from domain.entities.idea import Idea
from domain.value_objects.idea_status import IdeaStatus
from domain.exceptions.domain_exceptions import DomainException
from application.ports.incoming.i_idea_service import IIdeaService
from application.ports.outgoing.i_idea_repository import IIdeaRepository
from application.ports.outgoing.i_moderation_service import IModerationService


class IdeaUseCases(IIdeaService):
    """Реализация сценариев использования"""

    def __init__(
            self,
            idea_repository: IIdeaRepository,
            moderation_service: IModerationService
    ):
        self._repository = idea_repository
        self._moderation = moderation_service

    def create_idea(self, title: str, content: str, author_id: str, tags: List[str]) -> Idea:
        """Создать новую идею"""
        idea = Idea(
            id=str(uuid.uuid4()),
            title=title,
            content=content,
            author_id=author_id,
            tags=tags,
            status=IdeaStatus.DRAFT
        )

        # Пре-модерация перед сохранением
        if not self._moderation.check_content(idea):
            idea.reject("Content moderation failed")

        return self._repository.save(idea)

    def publish_idea(self, idea_id: str) -> Idea:
        """Опубликовать идею"""
        idea = self._repository.find_by_id(idea_id)
        if not idea:
            raise DomainException(f"Idea {idea_id} not found")

        # Финальная проверка перед публикацией
        if not self._moderation.check_content(idea):
            idea.reject("Final moderation failed")
        else:
            idea.publish()

        return self._repository.save(idea)

    def like_idea(self, idea_id: str, user_id: str) -> Idea:
        """Лайкнуть идею"""
        idea = self._repository.find_by_id(idea_id)
        if not idea:
            raise DomainException(f"Idea {idea_id} not found")

        idea.add_vote(user_id)
        return self._repository.save(idea)

    def get_idea(self, idea_id: str) -> Optional[Idea]:
        """Получить идею"""
        return self._repository.find_by_id(idea_id)


infrastructure / api / rest_controller.py

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from domain.exceptions.domain_exceptions import DomainException
from application.ports.incoming.i_idea_service import IIdeaService


# Pydantic модели для API
class CreateIdeaRequest(BaseModel):
    title: str
    content: str
    tags: List[str] = []


class IdeaResponse(BaseModel):
    id: str
    title: str
    content: str
    author_id: str
    tags: List[str]
    status: str
    likes_count: int


def setup_routes(app: FastAPI, idea_service: IIdeaService):
    """Настройка REST маршрутов"""

    @app.post("/api/ideas", response_model=IdeaResponse)
    async def create_idea(request: CreateIdeaRequest, user_id: str = "default_user"):
        """Создать новую идею"""
        try:
            idea = idea_service.create_idea(
                title=request.title,
                content=request.content,
                author_id=user_id,
                tags=request.tags
            )
            return _to_response(idea)
        except DomainException as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.post("/api/ideas/{idea_id}/publish", response_model=IdeaResponse)
    async def publish_idea(idea_id: str):
        """Опубликовать идею"""
        try:
            idea = idea_service.publish_idea(idea_id)
            return _to_response(idea)
        except DomainException as e:
            raise HTTPException(status_code=404, detail=str(e))

    @app.post("/api/ideas/{idea_id}/like", response_model=IdeaResponse)
    async def like_idea(idea_id: str, user_id: str = "liker_user"):
        """Лайкнуть идею"""
        try:
            idea = idea_service.like_idea(idea_id, user_id)
            return _to_response(idea)
        except DomainException as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.get("/api/ideas/{idea_id}", response_model=IdeaResponse)
    async def get_idea(idea_id: str):
        """Получить идею"""
        idea = idea_service.get_idea(idea_id)
        if not idea:
            raise HTTPException(status_code=404, detail="Idea not found")
        return _to_response(idea)


def _to_response(idea) -> IdeaResponse:
    return IdeaResponse(
        id=idea.id,
        title=idea.title,
        content=idea.content,
        author_id=idea.author_id,
        tags=idea.tags,
        status=idea.status.value,
        likes_count=idea.likes_count
    )
