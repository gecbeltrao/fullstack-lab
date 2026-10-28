"""Rota de inscrição a completar na atividade 3."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session


from app.db_session import find_event, get_session
from app.models import Registration, User


router = APIRouter()


class RegistrationInput(BaseModel):
    user_id: int


@router.post("/events/{event_id}/registrations", status_code=201)
def register(event_id: int, data: RegistrationInput, session: Session = Depends(get_session)):
    event = find_event(session, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Evento não encontrado")
    user = session.get(User, data.user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    existente = session.scalar(
        select(Registration).where(
            Registration.event_id == event_id,
            Registration.user_id == data.user_id,
        )
    )
    if existente is not None:
        raise HTTPException(status_code=409, detail="Usuário já inscrito neste evento")
    inscritos = session.scalar(
        select(func.count()).select_from(Registration).where(Registration.event_id == event_id)
    )
    if inscritos >= event.capacity:
        raise HTTPException(status_code=409, detail="Evento lotado")
    
    registration = Registration(event_id=event_id, user_id=data.user_id)
    session.add(registration)
    session.commit()
    return {"event_id": event_id, "user_id": data.user_id}
