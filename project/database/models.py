from typing import List, Optional
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel


class Insumo(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    descripcion: str
    presentacion: Optional[str] = Field(default=None)
    linea: str
    sublinea: str
    precio: float

    # Relationships
    detalles_venta: List["DetalleVenta"] = Relationship(back_populates="insumo")
    promociones_detalle: List["PromocionDetalle"] = Relationship(
        back_populates="insumo"
    )


class Cliente(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    nombre: str
    calle: str
    num_ext: int
    num_int: Optional[int] = Field(default=None)
    colonia: str
    municipio: str
    codigo_postal: str
    estado: str
    telefono: str
    nit: str
    contacto: Optional[str] = Field(default=None)

    # Relationships
    ventas: List["Venta"] = Relationship(back_populates="cliente")
    visitas_venta: List["ClienteVisitaVenta"] = Relationship(back_populates="cliente")
    visitas: List["ClienteVisita"] = Relationship(back_populates="cliente")


class Empleado(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    nombre: str
    apellido_paterno: str
    apellido_materno: str
    tipo: str

    # Relationships
    ventas: List["Venta"] = Relationship(back_populates="empleado")
    visitas_venta: List["ClienteVisitaVenta"] = Relationship(back_populates="empleado")
    concursos_ganadores: List["ConcursoGanadores"] = Relationship(
        back_populates="empleado"
    )


class Venta(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    fecha: str
    cliente_id: UUID = Field(foreign_key="cliente.id")
    monto: float
    empleado_id: UUID = Field(foreign_key="empleado.id")

    # Relationships
    empleado: "Empleado" = Relationship(back_populates="ventas")
    cliente: "Cliente" = Relationship(back_populates="ventas")
    detalles: List["DetalleVenta"] = Relationship(back_populates="venta")


class DetalleVenta(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)  # Added primary key
    venta_id: UUID = Field(foreign_key="venta.id")
    insumo_id: UUID = Field(foreign_key="insumo.id")
    cantidad: int
    precio: float

    # Relationships
    venta: "Venta" = Relationship(back_populates="detalles")
    insumo: "Insumo" = Relationship(back_populates="detalles_venta")


class ClienteVisita(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)  # Added primary Key
    cliente_id: UUID = Field(foreign_key="cliente.id")
    periodo_visita: str

    # Relationships
    cliente: "Cliente" = Relationship(back_populates="visitas")


class ClienteVisitaVenta(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    fecha: str
    cliente_id: UUID = Field(foreign_key="cliente.id")
    empleado_id: UUID = Field(foreign_key="empleado.id")
    observacion: Optional[str] = Field(default=None)

    # Relationships
    cliente: "Cliente" = Relationship(back_populates="visitas_venta")
    empleado: "Empleado" = Relationship(back_populates="visitas_venta")


class Promocion(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    linea: str
    titulo_promocion: str
    fecha_inicio: str
    fecha_fin: str
    condiciones: Optional[str] = Field(default=None)

    # Relationships
    detalles: List["PromocionDetalle"] = Relationship(back_populates="promocion")


class PromocionDetalle(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)  # Added primary key.
    promocion_id: UUID = Field(foreign_key="promocion.id")
    insumo_id: UUID = Field(foreign_key="insumo.id")
    descuento: float

    # Relationships
    promocion: "Promocion" = Relationship(back_populates="detalles")
    insumo: "Insumo" = Relationship(back_populates="promociones_detalle")


class Concurso(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    descripcion: str
    fecha_inicio: str
    fecha_fin: str
    premio: str

    # Relationships
    ganadores: List["ConcursoGanadores"] = Relationship(back_populates="concurso")


class ConcursoGanadores(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)  # Added primary key
    concurso_id: UUID = Field(foreign_key="concurso.id")
    empleado_id: UUID = Field(foreign_key="empleado.id")

    # Relationships
    concurso: "Concurso" = Relationship(back_populates="ganadores")
    empleado: "Empleado" = Relationship(back_populates="concursos_ganadores")


class MetaVentas(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tipo_empleado: str
    monto_venta: float
    bono_especial: float
    fecha_inicio: str
    fecha_fin: str
