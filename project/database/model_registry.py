from project.database.models import (
    Cliente,
    ClienteVisita,
    ClienteVisitaVenta,
    Concurso,
    ConcursoGanadores,
    DetalleVenta,
    Empleado,
    Insumo,
    MetaVentas,
    Promocion,
    PromocionDetalle,
    Venta,
)

MODEL_REGISTRY = {
    "insumo": {
        "model": Insumo,
        "fields": {
            "id": {"required": False, "type": "UUID"},
            "descripcion": {"required": True, "type": "str"},
            "presentacion": {"required": False, "type": "str", "default": None},
            "linea": {"required": True, "type": "str"},
            "sublinea": {"required": True, "type": "str"},
            "precio": {"required": True, "type": "float"},
        },
        "relationships": ["detalles_venta", "promociones_detalle"],
    },
    "cliente": {
        "model": Cliente,
        "fields": {
            "id": {"required": False, "type": "UUID"},
            "nombre": {"required": True, "type": "str"},
            "calle": {"required": True, "type": "str"},
            "num_ext": {"required": True, "type": "int"},
            "num_int": {"required": False, "type": "int", "default": None},
            "colonia": {"required": True, "type": "str"},
            "municipio": {"required": True, "type": "str"},
            "codigo_postal": {"required": True, "type": "int"},
            "estado": {"required": True, "type": "str"},
            "telefono": {"required": True, "type": "int"},
            "nit": {"required": True, "type": "str"},
            "contacto": {"required": False, "type": "str", "default": None},
        },
        "relationships": ["ventas", "visitas_venta", "visitas"],
    },
    "empleado": {
        "model": Empleado,
        "fields": {
            "id": {"required": False, "type": "UUID"},
            "nombre": {"required": True, "type": "str"},
            "apellido_paterno": {"required": True, "type": "str"},
            "apellido_materno": {"required": True, "type": "str"},
            "tipo": {"required": True, "type": "str"},
        },
        "relationships": ["ventas", "visitas_venta", "concursos_ganadores"],
    },
    "venta": {
        "model": Venta,
        "fields": {
            "id": {"required": False, "type": "UUID"},
            "fecha": {"required": True, "type": "str"},
            "cliente_id": {"required": True, "type": "UUID"},
            "monto": {"required": True, "type": "float"},
            "empleado_id": {"required": True, "type": "UUID"},
        },
        "relationships": ["detalles"],
    },
    "detalle_venta": {
        "model": DetalleVenta,
        "fields": {
            "id": {"required": False, "type": "UUID"},  # Added ID
            "venta_id": {"required": True, "type": "UUID"},
            "insumo_id": {"required": True, "type": "UUID"},
            "cantidad": {"required": True, "type": "int"},
            "precio": {"required": True, "type": "float"},
        },
        "relationships": [],
    },
    "cliente_visita": {
        "model": ClienteVisita,
        "fields": {
            "id": {"required": False, "type": "UUID"},  # Added ID
            "cliente_id": {"required": True, "type": "UUID"},
            "periodo_visita": {"required": True, "type": "str"},
        },
        "relationships": [],
    },
    "cliente_visita_venta": {
        "model": ClienteVisitaVenta,
        "fields": {
            "id": {"required": False, "type": "UUID"},
            "fecha": {"required": True, "type": "str"},
            "cliente_id": {"required": True, "type": "UUID"},
            "empleado_id": {"required": True, "type": "UUID"},
            "observacion": {
                "required": False,
                "type": "str",
                "default": None,
            },
        },
        "relationships": [],
    },
    "promocion": {
        "model": Promocion,
        "fields": {
            "id": {"required": False, "type": "UUID"},
            "linea": {"required": True, "type": "str"},
            "titulo_promocion": {"required": True, "type": "str"},
            "fecha_inicio": {"required": True, "type": "str"},
            "fecha_fin": {"required": True, "type": "str"},
            "condiciones": {
                "required": False,
                "type": "str",
                "default": None,
            },
        },
        "relationships": ["detalles"],
    },
    "promocion_detalle": {
        "model": PromocionDetalle,
        "fields": {
            "id": {"required": False, "type": "UUID"},  # Added ID
            "promocion_id": {"required": True, "type": "UUID"},
            "insumo_id": {"required": True, "type": "UUID"},
            "descuento": {"required": True, "type": "float"},
        },
        "relationships": [],
    },
    "concurso": {
        "model": Concurso,
        "fields": {
            "id": {"required": False, "type": "UUID"},
            "descripcion": {"required": True, "type": "str"},
            "fecha_inicio": {"required": True, "type": "str"},
            "fecha_fin": {"required": True, "type": "str"},
            "premio": {"required": True, "type": "str"},
        },
        "relationships": ["ganadores"],
    },
    "concurso_ganadores": {
        "model": ConcursoGanadores,
        "fields": {
            "id": {"required": False, "type": "UUID"},  # Added id
            "concurso_id": {"required": True, "type": "UUID"},
            "empleado_id": {"required": True, "type": "UUID"},
        },
        "relationships": [],
    },
    "meta_ventas": {
        "model": MetaVentas,
        "fields": {
            "id": {"required": False, "type": "UUID"},
            "tipo_empleado": {"required": True, "type": "str"},
            "monto_venta": {"required": True, "type": "float"},
            "bono_especial": {"required": True, "type": "float"},
            "fecha_inicio": {"required": True, "type": "str"},
            "fecha_fin": {"required": True, "type": "str"},
        },
        "relationships": [],
    },
}
