from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from enum import Enum
from ..value_objects.task_status import TaskStatus
from ..value_objects.priority import Priority
from ..value_objects.deadline import Deadline
from ..value_objects.assignment_info import AssignmentInfo
from ..events.domain_events import TaskCreated, TaskAssigned, TaskCompleted, DeadlineMissed
from ..exceptions.domain_exceptions import DomainException


@dataclass
class Task:
    """Агрегат Task - корень агрегата"""
    id: str
    title: str
    description: str
    priority: Priority
    deadline: Deadline
    status: TaskStatus = TaskStatus.TODO
    assignment: Optional[AssignmentInfo] = None
    archived: bool = False
    _events: List[DomainEvent] = field(default_factory=list, init=False)

    def assign(self, user_id: str, assigned_by: str) -> None:
        """Назначить задачу исполнителю"""
        if self.archived:
            raise DomainException("Cannot assign archived task")

        if self.status == TaskStatus.DONE:
            raise DomainException("Cannot assign completed task")

        # Проверка на dead users делается на уровне use case (репозиторий пользователей)
        # Домен получает уже валидированного пользователя

        self.assignment = AssignmentInfo(
            user_id=user_id,
            assigned_at=datetime.now(),
            assigned_by=assigned_by
        )

        if self.status == TaskStatus.TODO:
            self.status = TaskStatus.IN_PROGRESS

        self._add_event(TaskAssigned(
            task_id=self.id,
            user_id=user_id,
            assigned_by=assigned_by
        ))

    def update_status(self, new_status: TaskStatus) -> None:
        """Обновить статус задачи"""
        if self.archived:
            raise DomainException("Cannot update archived task")

        if self.status == TaskStatus.DONE:
            raise DomainException("Cannot update completed task")

        # Инвариант: нельзя закрыть таску без исполнителя
        if new_status == TaskStatus.DONE and not self.assignment:
            raise DomainException("Cannot complete task without assignee")

        self.status = new_status

        if new_status == TaskStatus.DONE:
            self._add_event(TaskCompleted(
                task_id=self.id,
                completed_at=datetime.now()
            ))

    def postpone_deadline(self, new_deadline: Deadline) -> None:
        """Перенести дедлайн"""
        if self.archived:
            raise DomainException("Cannot modify archived task")

        if self.status == TaskStatus.DONE:
            raise DomainException("Cannot modify completed task")

        # Инвариант: новый дедлайн не может быть раньше старого
        if new_deadline.is_before(self.deadline):
            raise DomainException("New deadline cannot be earlier than current")

        self.deadline = new_deadline

    def archive(self) -> None:
        """Архивировать задачу"""
        if self.archived:
            raise DomainException("Task already archived")

        self.archived = True

    def complete(self) -> None:
        """Завершить задачу (синтаксический сахар)"""
        self.update_status(TaskStatus.DONE)

    def is_overdue(self) -> bool:
        """Проверить просрочена ли задача"""
        return (self.status != TaskStatus.DONE and
                self.deadline.is_in_past())

    def check_deadline(self) -> None:
        """Проверить дедлайн и сгенерировать событие если просрочена"""
        if self.is_overdue():
            self._add_event(DeadlineMissed(
                task_id=self.id,
                deadline=self.deadline.value
            ))

    def _add_event(self, event: DomainEvent) -> None:
        """Добавить доменное событие"""
        self._events.append(event)

    def clear_events(self) -> List[DomainEvent]:
        """Очистить события (вызывается после сохранения)"""
        events = self._events.copy()
        self._events.clear()
        return events
