ERROR_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "success": {"type": "boolean", "example": False},
        "data": {"nullable": True},
        "error": {
            "type": "object",
            "properties": {
                "code": {"type": "string"},
                "message": {"type": "string"},
                "request_id": {"type": "string"},
                "field": {"type": "string"},
                "details": {"type": "object"},
            },
        },
        "request_id": {"type": "string"},
        "timestamp": {"type": "string", "format": "date-time"},
    },
}

SUCCESS_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "success": {"type": "boolean", "example": True},
        "data": {"type": "object"},
        "error": {"nullable": True},
        "request_id": {"type": "string"},
        "timestamp": {"type": "string", "format": "date-time"},
    },
}


def base_openapi_document(servers=None):
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "DxCon API",
            "version": "v1",
            "description": "DxCon external API platform for partners, labs, hospitals, and clinics.",
        },
        "servers": servers
        or [
            {"url": "http://localhost:5000", "description": "Local development"},
            {"url": "https://api.dxcon.local", "description": "Production"},
        ],
        "tags": [],
        "paths": {},
        "components": {
            "securitySchemes": {
                "ApiKeyAuth": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "X-API-Key",
                    "description": "Partner API key issued by DxCon API Platform",
                },
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                    "description": "JWT bearer token placeholder",
                },
            },
            "schemas": {
                "ErrorResponse": ERROR_RESPONSE_SCHEMA,
                "SuccessResponse": SUCCESS_RESPONSE_SCHEMA,
            },
        },
        "security": [{"ApiKeyAuth": []}, {"BearerAuth": []}],
    }


def operation_object(method: str, domain: str, path: str, deprecated: bool = False):
    return {
        "summary": f"{method} {path}",
        "tags": [domain],
        "deprecated": deprecated,
        "responses": {
            "200": {
                "description": "Successful response",
                "content": {"application/json": {"schema": {"$ref": "#/components/schemas/SuccessResponse"}}},
            },
            "400": {
                "description": "Validation error",
                "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}},
            },
            "401": {
                "description": "Unauthorized",
                "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}},
            },
            "404": {
                "description": "Not found",
                "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}},
            },
            "500": {
                "description": "Server error",
                "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}},
            },
        },
    }
