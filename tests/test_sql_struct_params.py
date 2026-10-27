from attio.models import ParametersStruct


def test_sql_struct_parameter_keeps_nested_fields() -> None:
    raw = {"type": "struct", "value": {"name": {"type": "string", "value": "Fundstack"}}}

    param = ParametersStruct.model_validate(raw)

    assert param.model_dump() == raw
