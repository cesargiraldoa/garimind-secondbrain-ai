from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from .base import Base

def now_utc():
    return datetime.now(timezone.utc)

class Proyecto(Base):
    __tablename__ = "proyectos"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(255), nullable=False)
    objetivo = Column(Text, nullable=True)
    estado = Column(String(50), default="activo")
    fecha_inicio = Column(DateTime, default=now_utc)

    tareas = relationship("Tarea", back_populates="proyecto")
    recuerdos = relationship("Recuerdo", back_populates="proyecto")

class Tarea(Base):
    __tablename__ = "tareas"
    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(255), nullable=False)
    responsable = Column(String(255), nullable=True)
    prioridad = Column(String(50), default="media")
    proyecto_id = Column(Integer, ForeignKey("proyectos.id"), nullable=True, index=True)
    fecha_limite = Column(DateTime, nullable=True)
    estado = Column(String(50), default="abierta")
    creada_en = Column(DateTime, default=now_utc)

    proyecto = relationship("Proyecto", back_populates="tareas")

class Recuerdo(Base):
    __tablename__ = "recuerdos"
    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String(50), default="profesional")  # personal, emocional, familiar, profesional
    contenido = Column(Text, nullable=False)
    fecha = Column(DateTime, default=now_utc)
    tags = Column(String(255), nullable=True)
    proyecto_id = Column(Integer, ForeignKey("proyectos.id"), nullable=True, index=True)
    doc_url = Column(String(512), nullable=True)

    proyecto = relationship("Proyecto", back_populates="recuerdos")

class Interaccion(Base):
    __tablename__ = "interacciones"
    id = Column(Integer, primary_key=True, index=True)
    usuario = Column(String(255), nullable=True)
    medio = Column(String(50), default="texto")  # texto, voz, whatsapp
    contenido = Column(Text, nullable=False)
    respuesta = Column(Text, nullable=True)
    fecha = Column(DateTime, default=now_utc)
