from fastmcp import FastMCP
from typing import Callable, Any

from fastmcp.utilities.types import FastMCPBaseModel
from fastmcp.tools.tool import ParsedFunction


class Template(FastMCPBaseModel):
    name: str
    description: str
    params: dict
    title: str
    template_function: Callable[..., Any]


class CustomFastMCP(FastMCP):
    _templates: dict[str, Callable] = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def template(self, title: str):
        def decorator(fn):
            parsed_function = ParsedFunction.from_function(fn)
            self._templates[parsed_function.name] = Template(
                name=parsed_function.name,
                description=parsed_function.description,
                params=parsed_function.input_schema,
                title=title,
                template_function=fn,
            )
            return fn
        return decorator

    def get_templates(self):
        return self._templates
    
    def get_template(self, name: str):
        return self._templates[name]


