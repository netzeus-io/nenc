from contextlib import asynccontextmanager
from fastapi import FastAPI
from config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Do some stuff on startup
    print("Loading datastores")
    sessions = []
    for datastore in settings.datastores:
        datastore_devices = datastore.load_netconf_servers()
        if not datastore_devices:
            continue

        sessions.extend(datastore_devices)

    # Post sessions to Redis
    print([x.host for x in sessions])

    yield
    # Do some stuff on exit
    print("exit")


app = FastAPI(lifespan=lifespan)
