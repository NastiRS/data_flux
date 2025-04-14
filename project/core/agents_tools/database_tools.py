import json
from typing import Any, Dict, List, Union
from uuid import UUID

from agents import function_tool
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, select

from project.core.ai_clients import anthropic_client
from project.database.config import engine
from project.database.model_registry import MODEL_REGISTRY
from project.utils.utils import normalize_text


@function_tool(strict_mode=False)
def database_tables_info() -> dict[str, dict[str, Any]]:
    """Use this function to retrieve the user's database information.
    Returns the database's tables to personalize assistance.
    """
    return MODEL_REGISTRY


def get_full_database() -> Union[Dict[str, List[Dict]], str]:
    """
    Retrieves all records from all tables in the database.

    Returns:
        Union[Dict[str, List[Dict]], str]: If data is found, returns a dictionary where:
            - keys are the model names (table names)
            - values are lists of dictionaries containing the records for each table
        If no data is found in any table, returns the string "No data found in the database."
        Handles database errors gracefully by returning an error message.
    """
    try:
        with Session(engine) as session:
            all_data = {}

            for model_name, model_info in MODEL_REGISTRY.items():
                model_class = model_info["model"]
                fields = model_info["fields"]

                records = session.exec(select(model_class)).all()

                records_json = []
                if records:
                    for record in records:
                        record_dict = {}
                        for field_name in fields.keys():
                            record_dict[field_name] = getattr(record, field_name)
                        records_json.append(record_dict)

                all_data[model_name] = records_json

            if not any(all_data.values()):
                return "No data found in the database."

            return all_data

    except SQLAlchemyError as e:
        return f"An error occurred while accessing the database: {str(e)}"


@function_tool(strict_mode=False)
async def get_tokens_count() -> Union[List[Dict], str]:
    data = get_full_database()
    response = await anthropic_client.messages.count_tokens(
        model="claude-3-7-sonnet-20250219",
        messages=[{"role": "user", "content": f"{data}"}],
    )
    return response.model_dump().get("input_tokens")


@function_tool(strict_mode=False)
def find_records(data: Any) -> Union[List[Dict], str]:
    """
    Searches for records in the database based on the provided model and criteria.
    Supports mass operations by allowing empty or partial criteria.

    Args:
        data: Can be either:
            - A dictionary with 'model_name' and 'criteria' keys
            - A JSON string containing those keys
            - A dictionary with a 'data' key containing either of the above

    Returns:
        Union[List[Dict], str]: A list of dictionaries representing matching records, or an error message.
    """
    try:
        # Parsing input data
        if isinstance(data, str):
            data = json.loads(data)

        if isinstance(data, dict) and "data" in data:
            if isinstance(data["data"], str):
                data = json.loads(data["data"])
            else:
                data = data["data"]

        model_name = data.get("model_name")
        criteria = data.get("criteria", {})

        if not model_name:
            return "Error: 'model_name' key is required in the input."

        model_info = MODEL_REGISTRY.get(model_name.lower())
        if not model_info:
            available_models = ", ".join(MODEL_REGISTRY.keys())
            return f"Error: Model not found. Available models: {available_models}"

        model_class = model_info["model"]
        fields_info = model_info["fields"]

        # Validate and convert criteria fields (if any provided)
        for field, value in criteria.items():
            if field not in fields_info:
                return f"Error: Field '{field}' does not exist in the model '{model_name}'."

            field_type = fields_info[field]["type"]
            try:
                # Convert UUID strings to UUID objects
                if field_type == "UUID" and isinstance(value, str):
                    criteria[field] = UUID(value)
                # Handle optional fields
                elif field_type.startswith("Optional[") and value is not None:
                    inner_type = field_type[9:-1]  # Extract type from Optional[type]
                    if inner_type == "str":
                        criteria[field] = normalize_text(str(value))
                    # Add more type conversions as needed
                elif field_type == "str" and value is not None:
                    criteria[field] = normalize_text(str(value))
            except ValueError as e:
                return f"Error: Invalid value for field '{field}': {str(e)}"

        with Session(engine) as session:
            query = select(model_class)

            # Apply filters only if criteria is provided
            for field, value in criteria.items():
                field_info = fields_info[field]

                # Handle string searches with LIKE
                if field_info["type"] == "str" and isinstance(value, str):
                    query = query.where(
                        func.lower(getattr(model_class, field)).like(f"%{value}%")
                    )
                # Handle foreign key relationships
                elif "foreign_key" in field_info:
                    query = query.where(getattr(model_class, field) == value)
                # Handle other types with exact matching
                else:
                    query = query.where(getattr(model_class, field) == value)

            records = session.exec(query).all()

            if not records:
                criteria_desc = (
                    "all records" if not criteria else f"criteria {criteria}"
                )
                return f"No records found in {model_name} matching {criteria_desc}."

            result = []
            for record in records:
                if hasattr(record, "to_dict"):
                    result.append(record.to_dict())
                else:
                    record_dict = {}
                    for field_name in fields_info.keys():
                        if hasattr(record, field_name):
                            value = getattr(record, field_name)
                            # Convert UUID to string for JSON serialization
                            if isinstance(value, UUID):
                                value = str(value)
                            record_dict[field_name] = value
                    result.append(record_dict)

            return result

    except json.JSONDecodeError as e:
        return f"Error parsing JSON: {str(e)}"
    except Exception as e:
        return f"Error searching records: {str(e)}"


@function_tool(strict_mode=False)
def find_records_with_complex_conditions(data: Any) -> Union[List[Dict], str]:
    try:
        if isinstance(data, str):
            data = json.loads(data)

        model_name = data.get("model_name")
        conditions = data.get("conditions", [])

        if not model_name or not conditions:
            return "Error: Both 'model_name' and 'conditions' are required."

        model_info = MODEL_REGISTRY.get(model_name.lower())
        if not model_info:
            return (
                f"Error: Model not found. Available: {', '.join(MODEL_REGISTRY.keys())}"
            )

        model_class = model_info["model"]
        fields_info = model_info["fields"]

        with Session(engine) as session:
            query = select(model_class)

            for condition in conditions:
                field = condition.get("field")
                operator = condition.get("operator")
                value = condition.get("value")

                if field not in fields_info:
                    return f"Error: Invalid field '{field}'"

                field_type = fields_info[field]["type"]
                field_attr = getattr(model_class, field)

                try:
                    if field_type == "UUID" and isinstance(value, str):
                        value = UUID(value)
                    elif field_type == "str" and value is not None:
                        value = normalize_text(str(value))

                    match operator:
                        case "eq":
                            if field_type == "str":
                                query = query.where(func.lower(field_attr) == value)
                            else:
                                query = query.where(field_attr == value)
                        case "neq":
                            if field_type == "str":
                                query = query.where(func.lower(field_attr) != value)
                            else:
                                query = query.where(field_attr != value)
                        case "gt":
                            query = query.where(field_attr > value)
                        case "gte":
                            query = query.where(field_attr >= value)
                        case "lt":
                            query = query.where(field_attr < value)
                        case "lte":
                            query = query.where(field_attr <= value)
                        case "like":
                            if field_type == "str":
                                query = query.where(
                                    func.lower(field_attr).like(f"%{value}%")
                                )
                            else:
                                query = query.where(field_attr.like(f"%{value}%"))
                        case "starts_with":
                            if field_type == "str":
                                query = query.where(
                                    func.lower(field_attr).like(f"{value}%")
                                )
                            else:
                                query = query.where(field_attr.like(f"{value}%"))
                        case "ends_with":
                            if field_type == "str":
                                query = query.where(
                                    func.lower(field_attr).like(f"%{value}")
                                )
                            else:
                                query = query.where(field_attr.like(f"%{value}"))
                        case _:
                            return f"Error: Invalid operator '{operator}'"

                except ValueError as e:
                    return f"Error converting value for field '{field}': {str(e)}"

            records = session.exec(query).all()

            if not records:
                return "No records found matching conditions"

            return [
                (
                    record.to_dict()
                    if hasattr(record, "to_dict")
                    else {
                        k: str(v) if isinstance(v, UUID) else v
                        for k, v in record.__dict__.items()
                        if not k.startswith("_")
                    }
                )
                for record in records
            ]

    except json.JSONDecodeError as e:
        return f"Error parsing JSON: {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"


@function_tool(strict_mode=False)
def insert_data(model_and_params: Dict[str, Any]) -> str:
    try:
        if isinstance(model_and_params, str):
            model_and_params = json.loads(model_and_params)

        model_name = model_and_params.get("model_name")
        model_params = model_and_params.get("params", {})

        if not model_name:
            return "Error: Model name is required."

        model_info = MODEL_REGISTRY.get(model_name.lower())
        if not model_info:
            return (
                f"Error: Model not found. Available: {', '.join(MODEL_REGISTRY.keys())}"
            )

        model_class = model_info["model"]
        fields = model_info["fields"]

        # Validate required fields
        missing_params = [
            field_name
            for field_name, details in fields.items()
            if details["required"] and field_name not in model_params
        ]
        if missing_params:
            return f"Missing parameters: {', '.join(missing_params)}"

        # Validate foreign keys
        with Session(engine) as session:
            for field_name, field_info in fields.items():
                if "foreign_key" in field_info and field_name in model_params:
                    ref_table, ref_field = field_info["foreign_key"].split(".")
                    ref_model = MODEL_REGISTRY[ref_table]["model"]
                    ref_exists = session.exec(
                        select(ref_model).where(
                            getattr(ref_model, ref_field) == model_params[field_name]
                        )
                    ).first()

                    if not ref_exists:
                        return f"Error: Referenced {ref_table} with {ref_field}={model_params[field_name]} not found"

            # Convert UUIDs
            for field_name, value in model_params.items():
                if fields[field_name]["type"] == "UUID" and isinstance(value, str):
                    try:
                        model_params[field_name] = UUID(value)
                    except ValueError:
                        return f"Invalid UUID format for {field_name}"

            instance = model_class(**model_params)
            session.add(instance)
            session.commit()

        return f"Successfully inserted {model_class.__name__}"

    except Exception as e:
        return f"Error: {str(e)}"


@function_tool(strict_mode=False)
def delete_a_data(data: Any) -> str:
    """
    Deletes records from the database based on the provided model and criteria.
    Supports mass deletion when no criteria is provided.

    Args:
        data (Any): A dictionary containing:
            - model_name (str): Name of the model/table to delete data from.
            - criteria (dict, optional): Key-value pairs for filtering records to delete.
                                      If empty, all records will be deleted.
    Returns:
        str: Confirmation message with the number of records deleted.
    """
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            return "Error: Invalid JSON format."

    model_name = data.get("model_name")
    criteria = data.get("criteria", {})

    if not model_name:
        return "Error: 'model_name' key is required in the input."

    model_info = MODEL_REGISTRY.get(model_name.lower())
    if not model_info:
        available_models = ", ".join(MODEL_REGISTRY.keys())
        return f"Error: Model not found. Available models: {available_models}"

    model_class = model_info["model"]
    fields_info = model_info["fields"]

    try:
        with Session(engine) as session:
            query = select(model_class)

            # Aplicar filtros solo si hay criterios
            if criteria:
                for field, value in criteria.items():
                    if field not in fields_info:
                        return f"Error: Field '{field}' does not exist in the model '{model_name}'."

                    field_type = fields_info[field]["type"]
                    # Aplicar lower() solo para campos de tipo string
                    if field_type == "str" and isinstance(value, str):
                        query = query.where(
                            func.lower(getattr(model_class, field)) == value.lower()
                        )
                    else:
                        query = query.where(getattr(model_class, field) == value)

            records = session.exec(query).all()

            if not records:
                criteria_desc = (
                    "all records" if not criteria else f"criteria {criteria}"
                )
                return f"No records found in {model_name} matching {criteria_desc}."

            count = 0
            for record in records:
                session.delete(record)
                count += 1

            session.commit()
            return f"Done! {count} records were deleted from {model_name}."

    except Exception as e:
        return f"Error deleting data: {str(e)}"


@function_tool(strict_mode=False)
def update_data(model_and_params: Dict[str, Any]) -> str:
    """
    Updates records in the database based on criteria.
    Supports mass updates when no identifier is provided.

    Args:
        model_and_params: A dictionary containing:
            - model_name: Name of the model/table to update
            - identifier (optional): Dictionary with field(s) to identify records to update
            - updates: Dictionary with the fields to update and their new values

    Returns:
        str: A message indicating success and number of records updated.
    """
    if isinstance(model_and_params, str):
        try:
            model_and_params = json.loads(model_and_params)
        except json.JSONDecodeError:
            return "Error: Invalid JSON format."

    model_name = model_and_params.get("model_name")
    identifier = model_and_params.get("identifier", {})
    updates = model_and_params.get("updates", {})

    if not all([model_name, updates]):
        return "Error: model_name and updates are required."

    model_info = MODEL_REGISTRY.get(model_name.lower())
    if not model_info:
        available_models = ", ".join(MODEL_REGISTRY.keys())
        return f"Error: Model not found. Available models: {available_models}"

    model_class = model_info["model"]
    fields_info = model_info["fields"]

    invalid_fields = [field for field in updates if field not in fields_info]
    if invalid_fields:
        return f"Error: Invalid fields for update: {', '.join(invalid_fields)}"

    try:
        with Session(engine) as session:
            query = select(model_class)

            # Aplicar filtros solo si hay identificador
            if identifier:
                for field, value in identifier.items():
                    if field not in fields_info:
                        return f"Error: Field '{field}' does not exist in the model '{model_name}'."

                    field_type = fields_info[field]["type"]
                    # Aplicar lower() solo para campos de tipo string
                    if field_type == "str" and isinstance(value, str):
                        query = query.where(
                            func.lower(getattr(model_class, field)) == value.lower()
                        )
                    else:
                        query = query.where(getattr(model_class, field) == value)

            records = session.exec(query).all()

            if not records:
                identifier_desc = (
                    "any records"
                    if not identifier
                    else f"records with identifier: {identifier}"
                )
                return f"No {identifier_desc} found to update"

            count = 0
            for record in records:
                for field, new_value in updates.items():
                    field_type = fields_info[field]["type"]
                    # Convertir a minúsculas solo si es un campo string
                    if field_type == "str" and isinstance(new_value, str):
                        new_value = new_value.lower()
                    setattr(record, field, new_value)
                count += 1

            session.commit()
            return f"Done! {count} records were updated in {model_name}."

    except Exception as e:
        return f"Error updating records: {str(e)}"
