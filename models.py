from typing import Union, Optional, List
from uuid import UUID
from enum import Enum
from pydantic import BaseModel, IPvAnyAddress


class DatasourceEnum(str, Enum):
    file = "file"
    api = "api"


class Datasource(BaseModel):
    type: DatasourceEnum


class FileDatasource(Datasource):
    type: DatasourceEnum = "file"
    file: str


class ApiDatasource(Datasource):
    type: DatasourceEnum = "api"
    url: str
    token: Optional[str]


class Worker(BaseModel):
    id: UUID
    auth_key: UUID
    sessions: List[UUID]


class SessionModeEnum(str, Enum):
    default = "default"
    replay = "replay"


class Session(BaseModel):
    host: Union[IPvAnyAddress, str]
    port: Optional[int] = 830
    username: Optional[str]
    password: Optional[str]
    filter: Optional[str]
    mode: SessionModeEnum = SessionModeEnum.default
    meta: Optional[dict] = {}
    session_id: Optional[UUID]
    netconf_session_id: Optional[int]
    assigned_worker: Optional[UUID]

    class Config:
        use_enum_values = True
