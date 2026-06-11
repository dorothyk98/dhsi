"""BLE scanning via bleak. The only module that touches bleak types."""

from bleak import BleakScanner

from identify import DeviceRecord


async def scan(duration: float = 10.0) -> list[DeviceRecord]:
    """Scan for `duration` seconds; return records sorted strongest-signal first."""
    found = await BleakScanner.discover(timeout=duration, return_adv=True)
    records = []
    for address, (device, adv) in found.items():
        records.append(
            DeviceRecord(
                address=address,
                name=adv.local_name or device.name,
                rssi=adv.rssi,
                tx_power=adv.tx_power,
                manufacturer_data=dict(adv.manufacturer_data),
                service_uuids=list(adv.service_uuids),
            )
        )
    records.sort(key=lambda r: r.rssi, reverse=True)
    return records
