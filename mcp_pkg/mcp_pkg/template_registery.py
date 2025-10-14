from typing import Any, Callable, Dict, Type, overload
from pydantic import BaseModel, ValidationError
from functools import wraps, partial
import inspect
import threading
from .schema import ToolTemplate


class TemplateRegistrationError(Exception):
    """Raised when template registration fails"""
    pass


class TemplateMixin:
    """
    Mixin class that provides dynamic template registration and rendering capabilities.
    
    Similar to the tool registration pattern (@server.tool), this allows decorating 
    functions as templates with support for:
    - Multiple calling patterns (@template, @template(), @template("name"), etc.)
    - Type-safe parameter validation via Pydantic models
    - Async and sync template functions
    - Thread-safe registration
    - Dynamic template rendering with validation
    
    Design Patterns Used:
    - **Factory Pattern**: Creates template instances from functions
    - **Registry Pattern**: Maintains centralized template storage
    - **Decorator Pattern**: Wraps functions to add template capabilities
    - **Strategy Pattern**: Handles sync/async rendering differently
    
    Example Usage:
        ```python
        class MyMCP(FastMCP, TemplateMixin):
            pass
        
        mcp = MyMCP()
        
        # Simple template
        @mcp.template
        def greeting(params):
            return f"Hello, {params.name}!"
        
        # Template with custom name and params model
        class GreetParams(BaseModel):
            name: str
            greeting: str = "Hi"
        
        @mcp.template(name="custom_greeting", params_model=GreetParams)
        def greet(params: GreetParams):
            return f"{params.greeting}, {params.name}!"
        
        # Render template
        result = mcp.render_template("greeting", {"name": "World"})
        ```
    """
    
    def __init__(self, *args, **kwargs):
        # Initialize template storage if not already present
        if not hasattr(self, '_templates'):
            self._templates: Dict[str, ToolTemplate] = {}
        if not hasattr(self, '_registry_lock'):
            self._registry_lock = threading.Lock()
        super().__init__(*args, **kwargs)
    
    def get_template(self, name: str) -> ToolTemplate:
        """
        Retrieve a registered template by name.
        
        Args:
            name: The template name to look up
            
        Returns:
            The ToolTemplate instance
            
        Raises:
            KeyError: If template is not found
        """
        with self._registry_lock:
            try:
                return self._templates[name]
            except KeyError:
                available = list(self._templates.keys())
                raise KeyError(
                    f"Template '{name}' not found. "
                    f"Available templates: {available if available else 'None'}"
                )

    def register_tool_template(self, template: ToolTemplate) -> None:
        """
        Register a template instance in the registry.
        
        Note: Named 'register_tool_template' to avoid conflicts with FastMCP's add_template method.
        
        Args:
            template: The ToolTemplate instance to register
            
        Raises:
            TemplateRegistrationError: If template name already exists
        """
        with self._registry_lock:
            if template.key in self._templates:
                raise TemplateRegistrationError(
                    f"Template '{template.name}' is already registered. "
                    f"Use a different name or unregister the existing template first."
                )
            self._templates[template.key] = template

    # Overloads for type hints (similar to tool() method)
    @overload
    def template(
        self,
        name_or_fn: Callable[..., Any],
        *,
        name: str | None = None,
        title: str | None = None,
        description: str | None = None,
        params_model: Type[BaseModel] | None = None,
    ) -> Callable[..., Any]: ...

    @overload
    def template(
        self,
        name_or_fn: str | None = None,
        *,
        name: str | None = None,
        title: str | None = None,
        description: str | None = None,
        params_model: Type[BaseModel] | None = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]: ...

    def template(
        self,
        name_or_fn: str | Callable[..., Any] | None = None,
        *,
        name: str | None = None,
        title: str | None = None,
        description: str | None = None,
        params_model: Type[BaseModel] | None = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]] | Callable[..., Any]:
        """
        Decorator to register a template function (similar to @server.tool).
        
        This decorator supports multiple calling patterns:
        - @mcp.template (without parentheses)
        - @mcp.template() (with empty parentheses)
        - @mcp.template("custom_name") (with name as first argument)
        - @mcp.template(name="custom_name") (with name as keyword argument)
        - @mcp.template(params_model=MyModel) (with parameter model)
        - mcp.template(function, name="custom") (direct function call)
        
        Args:
            name_or_fn: Either a function (when used as @template), a string name, or None
            name: Optional name for the template (keyword-only)
            title: Optional title for the template
            description: Optional description of what the template does
            params_model: Pydantic BaseModel subclass defining template parameters
            
        Returns:
            Either the wrapped function or a decorator function
            
        Raises:
            TemplateRegistrationError: If registration fails
            TypeError: If arguments are invalid
            
        Examples:
            ```python
            # Simple template without parameters
            @mcp.template
            def hello_template(params):
                return f"Hello, {params.name}!"
            
            # Template with custom name
            @mcp.template("greeting")
            def my_greeting(params):
                return f"Hi, {params.name}!"
            
            # Template with parameter model
            class GreetingParams(BaseModel):
                name: str
                greeting: str = "Hello"
            
            @mcp.template(params_model=GreetingParams)
            def custom_greeting(params: GreetingParams):
                return f"{params.greeting}, {params.name}!"
            
            # Async template
            @mcp.template
            async def async_template(params):
                await some_async_operation()
                return result
            
            # Direct registration
            def my_func(params):
                return "result"
            mcp.template(my_func, name="my_template", params_model=MyModel)
            ```
        """
        # Validate that the function follows template conventions
        def validate_template_function(fn: Callable) -> None:
            """Validate that function is suitable as a template"""
            if not (inspect.isfunction(fn) or inspect.iscoroutinefunction(fn)):
                raise TemplateRegistrationError(
                    "Template decorator must be applied to a function or coroutine function"
                )
            
            # Check function signature
            sig = inspect.signature(fn)
            params = list(sig.parameters.values())
            
            # Template function should accept at least one parameter (the params object)
            if len(params) == 0:
                raise TemplateRegistrationError(
                    f"Template function '{fn.__name__}' must accept at least one parameter "
                    f"(the params object). Example: def template_fn(params): ..."
                )

        # Determine the actual name and function based on the calling pattern
        if inspect.isroutine(name_or_fn):
            # Case 1: @template (without parens) - function passed directly
            # Case 2: direct call like template(fn, name="something")
            fn = name_or_fn
            template_name = name  # Use keyword name if provided, otherwise use function name
            
            validate_template_function(fn)
            
            # Extract or infer template information
            final_name = template_name or fn.__name__
            final_title = title or fn.__name__.replace('_', ' ').title()
            final_description = description or fn.__doc__ or f"Template: {final_name}"
            is_async = inspect.iscoroutinefunction(fn)
            
            # If no params_model provided, try to infer from function signature
            if params_model is None:
                sig = inspect.signature(fn)
                first_param = list(sig.parameters.values())[0]
                if first_param.annotation != inspect.Parameter.empty:
                    # Try to use the annotation as params_model
                    if isinstance(first_param.annotation, type) and issubclass(first_param.annotation, BaseModel):
                        params_model = first_param.annotation
                    else:
                        # Create a generic params model
                        params_model = BaseModel
                else:
                    # No annotation, use generic BaseModel
                    params_model = BaseModel
            
            # Create and register the template
            tool_template = ToolTemplate(
                name=final_name,
                description=final_description,
                inputSchema=params_model,
                title=final_title,
                template_fn=fn,
                is_async=is_async,
            )
            
            self.register_tool_template(tool_template)
            
            # Return the original function wrapped to preserve functionality
            @wraps(fn)
            def wrapper(*args, **kwargs):
                return fn(*args, **kwargs)
            
            # Attach template metadata to the function
            wrapper._template = tool_template  # type: ignore
            wrapper._template_name = final_name  # type: ignore
            
            return wrapper

        elif isinstance(name_or_fn, str):
            # Case 3: @template("custom_name") - name passed as first argument
            if name is not None:
                raise TypeError(
                    "Cannot specify both a name as first argument and as keyword argument. "
                    f"Use either @template('{name_or_fn}') or @template(name='{name}'), not both."
                )
            template_name = name_or_fn
        elif name_or_fn is None:
            # Case 4: @template() or @template(name="something") - use keyword name
            template_name = name
        else:
            raise TypeError(
                f"First argument to @template must be a function, string, or None, got {type(name_or_fn)}"
            )

        # Return decorator for cases where we need to wait for the function
        return partial(
            self.template,
            name=template_name,
            title=title,
            description=description,
            params_model=params_model,
        )
    
    async def render_template_async(
        self, 
        name: str, 
        raw_params: Dict[str, Any], 
        **extra_kwargs
    ) -> Any:
        """
        Render an async template with validated parameters.
        
        Args:
            name: Name of the template to render
            raw_params: Raw parameter dictionary to validate and pass to template
            **extra_kwargs: Additional keyword arguments to pass to template function
            
        Returns:
            The result of the template function
            
        Raises:
            KeyError: If template not found
            ValidationError: If parameters don't match the template's model
        """
        tpl = self.get_template(name)
        model = tpl.inputSchema
        
        # Validate parameters against the model
        try:
            if isinstance(model, type) and issubclass(model, BaseModel) and model is not BaseModel:
                # Only validate if it's a BaseModel subclass, not BaseModel itself
                params_obj = model.model_validate(raw_params)
            else:
                # For BaseModel itself or non-BaseModel, pass raw params
                params_obj = type('Params', (), raw_params)() if raw_params else type('Params', (), {})()
        except ValidationError as e:
            raise ValidationError(
                f"Parameter validation failed for template '{name}': {e}"
            ) from e
        
        fn = tpl.template_fn
        
        # Handle sync functions in async context
        if not tpl.is_async:
            # Run sync function synchronously (caller handles async context)
            return fn(params_obj, **extra_kwargs)
        
        # Execute async template
        return await fn(params_obj, **extra_kwargs)
    
    def render_template(
        self, 
        name: str, 
        raw_params: Dict[str, Any], 
        extra_kwargs: Dict[str, Any]
    ) -> Any:
        """
        Render a sync template with validated parameters.
        
        Args:
            name: Name of the template to render
            raw_params: Raw parameter dictionary to validate and pass to template
            **extra_kwargs: Additional keyword arguments to pass to template function
            
        Returns:
            The result of the template function
            
        Raises:
            KeyError: If template not found
            ValidationError: If parameters don't match the template's model
            RuntimeError: If template is async (use render_template_async instead)
        """
        tpl = self.get_template(name)
        model = tpl.inputSchema
        
        # Validate parameters against the model
        try:
            if isinstance(model, type) and issubclass(model, BaseModel) and model is not BaseModel:
                # Only validate if it's a BaseModel subclass, not BaseModel itself
                params_obj = model.model_validate(raw_params)
            else:
                # For BaseModel itself or non-BaseModel, pass raw params
                params_obj = type('Params', (), raw_params)() if raw_params else type('Params', (), {})()
        except ValidationError as e:
            raise ValidationError(
                f"Parameter validation failed for template '{name}': {e}"
            ) from e
        
        fn = tpl.template_fn
        
        # Ensure template is not async
        if tpl.is_async:
            raise RuntimeError(
                f"Template '{name}' is async. Use render_template_async() instead."
            )
        
        # Execute sync template
        return fn(params_obj, **extra_kwargs)

    def list_templates(self) -> list[Dict[str, Any]]:
        """
        List all registered templates with their schemas.
        
        Returns:
            List of dictionaries containing template metadata and parameter schemas
        """
        with self._registry_lock:
            templates = []
            for name, template in self._templates.items():
                template_info = {
                    "name": template.name,
                    "title": template.title,
                    "description": template.description,
                    "is_async": template.is_async,
                }
                
                # Add parameter schema if available
                if isinstance(template.inputSchema, type) and issubclass(template.inputSchema, BaseModel):
                    # Only call model_json_schema on subclasses, not BaseModel itself
                    if template.inputSchema is not BaseModel:
                        template_info["inputSchema"] = template.inputSchema.model_json_schema()
                    else:
                        template_info["inputSchema"] = {"type": "object", "properties": {}}
                
                templates.append(template_info)
            
            return templates

    def get_template_count(self) -> int:
        """Get the number of registered templates"""
        with self._registry_lock:
            return len(self._templates)
    
    def unregister_template(self, name: str) -> bool:
        """
        Unregister a template by name.
        
        Args:
            name: Name of template to remove
            
        Returns:
            True if template was removed, False if not found
        """
        with self._registry_lock:
            if name in self._templates:
                del self._templates[name]
                return True
            return False
    
    def clear_templates(self) -> None:
        """Remove all registered templates"""
        with self._registry_lock:
            self._templates.clear()
