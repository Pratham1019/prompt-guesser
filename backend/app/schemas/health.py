from pydantic import BaseModel


class HealthCheckSchema(BaseModel):
    """
    Pydantic schema representing the health check response.
    """

    status: str
    environment: str
    database: str
