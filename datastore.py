from typing import List
from pathlib import Path
from loguru import logger
from models import Session, FileDatasource, ApiDatasource, Datasource
import csv
import pynetbox


class GenericDataStore:
    """Generic DataStore which should be inherited by all DataStore implementations"""

    def __init__(self, ds: Datasource):
        self.ds = ds

    def load_netconf_servers(self) -> List[Session]:
        raise NotImplementedError


class FileDataStore(GenericDataStore):
    """Builds Session data from a local CSV file"""

    def __init__(self, ds: FileDatasource, **kwargs):
        super().__init__(ds=ds, **kwargs)

    def load_netconf_servers(self) -> List[Session]:
        source_file = Path(self.ds.file)
        if not source_file.exists():
            logger.error(
                f"Unable to load file '{self.ds.file}' (FileDataStore) because it was not found"
            )
            raise FileNotFoundError

        devices = []
        with source_file.open() as csv_file:
            csv_data = csv.DictReader(csv_file)
            for device in csv_data:
                devices.append(
                    Session(
                        host=device["host"],
                        port=device["port"] if device.get("port") else None,
                        username=device["username"] if device.get("username") else None,
                        password=device["password"] if device.get("password") else None,
                        filter=device["filter"] if device.get("filter") else None,
                        mode=device["mode"] if device.get("mode") else "default",
                    )
                )

        return devices


class ApiDataStore(GenericDataStore):
    """Builds Session data from a remote API, note this
    class should not be used directly but inherited by other
    API specific classes, eg. like NetboxDataStore"""

    def __init__(self, ds: ApiDatasource):
        self.ds = ds

    def load_netconf_servers(self) -> List[Session]:
        raise NotImplementedError


class NetboxDataStore(GenericDataStore):
    """Builds Session data from Netbox API using pynetbox module"""

    def __init__(
        self,
        ds: ApiDatasource,
        dcim_device_filter: dict = {},
        prefer_ipv6: bool = True,
        **kwargs,
    ):
        self.dcim_device_filter = dcim_device_filter
        self.prefer_ipv6 = prefer_ipv6
        super().__init__(ds=ds, **kwargs)

    def load_netconf_servers(self) -> List[Session]:
        api = pynetbox.api(url=self.ds.url, token=self.ds.token)
        try:
            api.status()
            logger.success(
                f"Gathered status from netbox instance {self.ds.url}, attempting to gather devices"
            )
        except Exception as err:
            logger.error(f"Unable to contact Netbox instance {self.ds.url}")
            raise SystemError(f"Unable to contact Netbox instance {self.ds.url}")

        devices = []
        filtered_devices = api.dcim.devices.filter(**self.dcim_device_filter)
        for device in filtered_devices:
            if not device.primary_ip:
                logger.error(
                    f"Unable to gather Primary IP details for device {device.name}"
                )
                continue

            if self.prefer_ipv6:
                if not device.primary_ip6:
                    logger.error(
                        f"Unable to gather Primary IPv6 address for device {device.name}"
                    )
                    raise SystemError(
                        "You are what is wrong with the world, ensure IPv6 is configured properly on the device in Netbox (primary ipv6) and you won't see this error again"
                    )

                primary_ip = device.primary_ip6.address.split("/")[0]
            else:
                primary_ip = device.primary_ip4.address.split("/")[0]

            devices.append(Session(host=primary_ip))
            break

        return devices
