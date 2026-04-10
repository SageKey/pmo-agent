Perform a Clean Architecture dependency audit across the project or specified directory.

## Instructions

1. Map the project's directory structure and identify which directories/modules correspond
   to which architectural layer:
   - Entities (domain models, business rules)
   - Use Cases (services, application logic)
   - Interface Adapters (routes, controllers, repositories, serializers)
   - Frameworks & Drivers (config, DB setup, external SDKs)

2. For each layer, scan import statements and flag any dependency rule violations:
   - Entities importing from adapters, frameworks, or use cases
   - Use cases importing from adapters or frameworks
   - Interface adapters importing from frameworks (acceptable) but also check for
     adapter-to-adapter coupling

3. Check for these common Python anti-patterns:
   - SQLAlchemy/Django ORM models used as domain entities
   - Flask/FastAPI request/response objects passed into service functions
   - `os.environ` or settings modules accessed inside domain or service code
   - Raw dicts crossing layer boundaries instead of typed DTOs
   - Circular imports (often a sign of layer violations)

4. Produce a dependency map showing:
   - Each module/package and its identified layer
   - Inward violations (❌) and clean dependencies (✅)
   - Modules that don't clearly belong to any layer

5. Prioritize findings by impact: which violations, if fixed, would most reduce coupling?

6. End with a recommended refactoring sequence — what to fix first and why.

Target directory: $ARGUMENTS
