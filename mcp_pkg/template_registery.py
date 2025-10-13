from typing import Any, Callable, Dict, Type
from pydantic import BaseModel, ValidationError
from functools import wraps
import inspect
import threading
from .schema import ToolTemplate

# Registry (thread-safe)
_templates: Dict[str, Dict[str, Any]] = {}
_registry_lock = threading.Lock()


class TemplateRegistrationError(Exception):
    ...


class TemplateMixin(object):
    _templates: dict[str, ToolTemplate] = {}
    _registry_lock = threading.Lock()

    def get_template(self, name: str) -> ToolTemplate:
        try:
            return self._templates[name]
        except KeyError:
            raise KeyError(f"Unknown template '{name}'")

    @staticmethod
    def template(self, name: str, params_model: Type[BaseModel]):
        """
        Register a template by name with explicit params model (a pydantic BaseModel subclass).
        Decorator returns the original function. The function should accept one arg: `params` (the model instance) or (params, **kwargs).
        """
        def decorator(fn: Callable[..., Any]):
            if not inspect.isfunction(fn) and not inspect.iscoroutinefunction(fn):
                raise TemplateRegistrationError("template decorator must be applied to a function or coroutine")

            with self._registry_lock:
                if name in self._templates:
                    raise TemplateRegistrationError(f"Template '{name}' already registered")

                # self._templates[name] = {
                #     "fn": fn,
                #     "params_model": params_model,
                #     "is_async": inspect.iscoroutinefunction(fn),
                #     "doc": fn.__doc__ or ""
                # }
                self._templates[name] = ToolTemplate(
                    name=name,
                    description=fn.__doc__ or "",
                    params=params_model,
                    title=fn.__name__,
                    template_fn=fn,
                    is_async=inspect.iscoroutinefunction(fn),
                )

            @wraps(fn)
            def wrapper(*args, **kwargs):
                # wrapper is optional; we keep original fn usable directly
                return fn(*args, **kwargs)
            return wrapper
        return decorator
    
    async def render_template_async(
        self, name: str, raw_params: Dict[str, Any], **extra_kwargs
    ):
        tpl = self.get_template(name)
        model = tpl.params
        try:
            params_obj = model.parse_obj(raw_params)
        except ValidationError as e:
            raise e
        fn = tpl.template_fn
        if not tpl.is_async:
            # run sync function in event loop's default executor if desired, but for simplicity:
            return fn(params_obj, **extra_kwargs)
        return await fn(params_obj, **extra_kwargs)
    
    def render_template(
        self, name: str, raw_params: Dict[str, Any], **extra_kwargs
    ):
        tpl = self.get_template(name)
        model = tpl.params
        try:
            params_obj = model.parse_obj(raw_params)
        except ValidationError as e:
            raise e
        fn = tpl.template_fn
        if tpl.is_async:
            # Caller must await render_template_async if template is async
            raise RuntimeError("Template is async; use render_template_async")
        return fn(params_obj, **extra_kwargs)

    def list_templates(self):
        return list({
            "name": name,
            "description": template.description,
            **template.params.model_json_schema(),
        } for name, template in self._templates.items())
        
