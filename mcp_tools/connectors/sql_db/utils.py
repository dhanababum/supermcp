from fastmcp import FastMCP
from typing import Callable
import inspect
from fastmcp.utilities.types import FastMCPBaseModel, get_cached_typeadapter
from fastmcp.tools.tool import ParsedFunction


def get_params(fn: Callable):
    return 

def get_description(fn: Callable):
    return get_cached_typeadapter(fn).json_schema(mode="serialization")

class Template(FastMCPBaseModel):
    name: str
    description: str
    params: dict


class CustomFastMCP(FastMCP):
    _templates: dict[str, Callable] = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def template(self, name: str):
        def decorator(fn):
            self._templates[name] = fn
            return fn
        return decorator

    def get_templates(self):
        _templates = {}
        for function_name, template_function in self._templates.items():
            parsed_function = ParsedFunction.from_function(template_function)
            _templates[parsed_function.name] = Template(
                name=parsed_function.name,
                description=parsed_function.description,
                params=parsed_function.input_schema,
            )
        return _templates
