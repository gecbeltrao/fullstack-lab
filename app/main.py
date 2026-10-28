"""API de eventos usada em todas as etapas do projeto."""

from datetime import date

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

import app.models
from app.database import Base, make_engine
from app.db_session import find_event, get_session
from app.models import Event, Registration
from app.registrations import router   # no topo, junto dos outros imports do app


class EventInput(BaseModel):
    """Dados enviados pelo cliente ao cadastrar um evento."""

    title: str
    date: date
    capacity: int


def create_app(database_url: str = "sqlite://") -> FastAPI:
    """Cria uma API com dados isolados para cada execução ou teste."""
    app = FastAPI(title="Eventos do Trilha")
    engine = make_engine(database_url)
    Base.metadata.create_all(engine)
    app.state.engine = engine

    def event_to_dict(session, event):
        inscritos = session.scalar(
            select(func.count()).select_from(Registration).where(Registration.event_id == event.id)
        )
        return {
            "id": event.id,
            "title": event.title,
            "date": event.date.isoformat(),
            "capacity": event.capacity,
            "available_slots": event.capacity - inscritos,
        }

    @app.get("/events")
    def list_events(session: Session = Depends(get_session)):
        eventos = session.scalars(select(Event)).all()
        return [event_to_dict(session, event) for event in eventos]

    @app.get("/events/{event_id}")
    def get_event(event_id: int, session: Session = Depends(get_session)):
        event = find_event(session, event_id)
        if event is None:
            raise HTTPException(status_code=404, detail="Evento não encontrado")
        return event_to_dict(session, event)

    @app.post("/events", status_code=201)
    def create_event(data: EventInput, session: Session = Depends(get_session)):
        if not data.title.strip():
            raise HTTPException(status_code=422, detail="O título não pode ser vazio")
        if data.capacity <= 0:
            raise HTTPException(status_code=422, detail="A capacidade deve ser maior que zero")

        event = Event(title=data.title, date=data.date, capacity=data.capacity)

        session.add(event)
        session.commit()

        return event_to_dict(session, event)

    app.include_router(router)

    return app


app = create_app("sqlite:///events.db")