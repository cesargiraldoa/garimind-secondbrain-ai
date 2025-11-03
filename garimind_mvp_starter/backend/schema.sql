-- GariMind MVP schema (PostgreSQL)
CREATE TABLE IF NOT EXISTS proyectos (
  id SERIAL PRIMARY KEY,
  nombre VARCHAR(255) NOT NULL,
  objetivo TEXT,
  estado VARCHAR(50) DEFAULT 'activo',
  fecha_inicio TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tareas (
  id SERIAL PRIMARY KEY,
  titulo VARCHAR(255) NOT NULL,
  responsable VARCHAR(255),
  prioridad VARCHAR(50) DEFAULT 'media',
  proyecto_id INTEGER REFERENCES proyectos(id) ON DELETE SET NULL,
  fecha_limite TIMESTAMP WITH TIME ZONE,
  estado VARCHAR(50) DEFAULT 'abierta',
  creada_en TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS recuerdos (
  id SERIAL PRIMARY KEY,
  tipo VARCHAR(50) DEFAULT 'profesional',
  contenido TEXT NOT NULL,
  fecha TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  tags VARCHAR(255),
  proyecto_id INTEGER REFERENCES proyectos(id) ON DELETE SET NULL,
  doc_url VARCHAR(512)
);

CREATE TABLE IF NOT EXISTS interacciones (
  id SERIAL PRIMARY KEY,
  usuario VARCHAR(255),
  medio VARCHAR(50) DEFAULT 'texto',
  contenido TEXT NOT NULL,
  respuesta TEXT,
  fecha TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
