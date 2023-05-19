from pydantic import BaseSettings, RedisDsn
from models import SessionModeEnum, FileDatasource, ApiDatasource
from datastore import FileDataStore, NetboxDataStore


class Settings(BaseSettings):
    # Default Settings to pass into Ncclient when attempting to establish a session with the NETCONF servers
    # Ideally if using RADIUS or TACACS+, provide the credentials in the .env file and they will be preferred
    # over the default settings in this file
    default_port: int = 830
    default_username: str = "my-username"
    default_password: str = "my-password"
    default_session_mode: SessionModeEnum = "default"
    default_netconf_timeout: int = 30
    default_hostkey_verify: bool = False

    # Configure Datastores here to distribute the connection details down to workers
    # and allow the controller to assign devices to multiple workers
    datastores = [
        FileDataStore(FileDatasource(file="devices.csv")),
        NetboxDataStore(
            ApiDatasource(
                url="https://netbox.example.com",
                token="my-super-secure-token",
            ),
            dcim_device_filter={
                "role": ["mpls-pe", "core-router"],
                "status": "active",
            },
        ),
    ]

    # How many threads will a single worker create
    # Note that a worker by default uses its main thread as the 'control' thread so
    # if worker_threads is set to 15, this is 15 separate NETCONF sessions it can handle
    # alongside the main thread which is responsible for listening to a redis pubsub channel
    # to deal with spawning and terminating new threads aka NETCONF sessions, think of it
    # like a control-plane thread
    worker_threads: int = 15

    # The worker will attempt to report some basic statistics to the controller every x amount
    # of seconds (default: 300s)
    time_to_report_mins: int = 300

    # If the number of NETCONF events passes this number before the next report time, the worker will
    # report basic statistics to the controller so it can determine if the worker is being overworked
    # and is not performing as expected
    max_events_before_checkin: int = 1200

    # Redis is used to distribute job information so that workers don't attempt to connect to the same
    # NETCONF server and cause duplicate NETCONF events in your output plugin
    redis: RedisDsn = "redis://redis:6379"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
