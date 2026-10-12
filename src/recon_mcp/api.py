"""HTTP interface of enum_ports (spec 001-enum-ports.md, Interface and Input Validation)."""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, StrictInt, StrictStr

from recon_mcp import scanner, scope

MIN_PORT = 1
MAX_PORT = 65535

HTTP_BAD_REQUEST = 400
HTTP_FORBIDDEN = 403
HTTP_INTERNAL_ERROR = 500

INVALID_REQUEST = "invalid_request"
INVALID_TARGET = "invalid_target"
INVALID_PORTS = "invalid_ports"
TARGET_NOT_ALLOWED = "target_not_allowed"
INVALID_SCOPE_FILE = "invalid_scope_file"


class ScanRequest(BaseModel):
    target: StrictStr
    ports: list[StrictInt]


class ScanResponse(BaseModel):
    target: str
    open_ports: list[int]


app = FastAPI(title="recon-mcp")


def error_response(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}})


@app.exception_handler(RequestValidationError)
async def handle_invalid_request(_: Request, __: RequestValidationError) -> JSONResponse:
    return error_response(
        HTTP_BAD_REQUEST,
        INVALID_REQUEST,
        "Body must be JSON with a string 'target' and an integer array 'ports'.",
    )


def are_valid_ports(ports: list[int]) -> bool:
    return bool(ports) and all(MIN_PORT <= port <= MAX_PORT for port in ports)


@app.post("/scan", response_model=ScanResponse)
async def scan(request: ScanRequest) -> ScanResponse | JSONResponse:
    target = scope.parse_target(request.target)
    if target is None:
        return error_response(
            HTTP_BAD_REQUEST,
            INVALID_TARGET,
            f"Target {request.target} is neither an IP address nor localhost.",
        )
    if not are_valid_ports(request.ports):
        return error_response(
            HTTP_BAD_REQUEST,
            INVALID_PORTS,
            f"Ports must be a non-empty list of integers from {MIN_PORT} to {MAX_PORT}.",
        )
    try:
        entries = scope.load_scope_entries()
    except scope.ScopeFileError as error:
        return error_response(HTTP_INTERNAL_ERROR, INVALID_SCOPE_FILE, str(error))
    if not scope.is_in_scope(target, entries):
        return error_response(
            HTTP_FORBIDDEN, TARGET_NOT_ALLOWED, f"Target {request.target} is not in scope."
        )
    open_ports = await scanner.find_open_ports(str(target), request.ports)
    return ScanResponse(target=request.target, open_ports=open_ports)
