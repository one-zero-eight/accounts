__all__ = ["CustomDocument", "CustomLink"]

from typing import Type, Any, TypeVar, get_args

from beanie import Document, PydanticObjectId, Link
from beanie.odm.registry import DocsRegistry
from pydantic import Field, ConfigDict, GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema


class CustomDocument(Document):
    model_config = ConfigDict(json_schema_extra={})

    id: PydanticObjectId | None = Field(default=None, description="MongoDB document ObjectID", serialization_alias="id")

    class Settings:
        keep_nulls = False
        max_nesting_depth = 1


D = TypeVar("D", bound=Document)


class CustomLink(Link[D]):
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Type[Any], handler: GetCoreSchemaHandler) -> CoreSchema:
        document_class = DocsRegistry.evaluate_fr(get_args(source_type)[0])
        document_class: Type[Document]

        serialization_schema = core_schema.plain_serializer_function_ser_schema(
            lambda instance: cls.serialize(instance),
            return_schema=core_schema.union_schema(
                [
                    core_schema.typed_dict_schema(
                        {
                            "id": core_schema.typed_dict_field(core_schema.str_schema()),
                            "collection": core_schema.typed_dict_field(core_schema.str_schema()),
                        }
                    ),
                    document_class.__pydantic_core_schema__,
                ],
            ),
        )

        schema = core_schema.json_or_python_schema(
            python_schema=core_schema.with_info_plain_validator_function(cls.build_validation(handler, source_type)),
            json_schema=core_schema.with_default_schema(core_schema.str_schema(), default="5eb7cf5a86d9755df3a6c593"),
            serialization=serialization_schema,
        )

        return schema
