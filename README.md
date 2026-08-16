# eltako-modbus

Read an **Eltako DSZ15DZMOD** three-phase energy meter over Modbus.

The DSZ15DZMOD (sold as the DSZ15DZMOD-3x80A) is a DIN-rail three-phase kWh
meter. It reports per-phase voltage, current, active power and power factor, the
three-phase totals, and four energy counters. It is Eltako's only Modbus meter;
the rest of the DSZ/WSZ range is S0-pulse or EnOcean.

This is a device library built on
[modbus-connection](https://github.com/balloob/modbus-connection). It takes a
`ModbusUnit` and never opens a connection of its own — the consumer owns the
link, and so chooses the transport.

The meter itself speaks Modbus RTU on RS-485, at 9600 baud, 8 data bits, 1 stop
bit and no parity unless it has been reconfigured. Reach it over a serial
adapter with those line settings, or over TCP through a gateway such as Eltako's
ZGW16WL-IP, which fronts up to sixteen of these meters. Nothing in this library
depends on which of the two you use.

## Install

```bash
pip install eltako-modbus
```

## Usage

```python
import asyncio

from modbus_connection import ModbusSerialParams
from modbus_connection.tmodbus import ModbusConnection

from eltako_modbus import Dsz15dzmod


async def main() -> None:
    connection = ModbusConnection(ModbusSerialParams(device="/dev/ttyUSB0"))
    try:
        meter = Dsz15dzmod(connection.for_unit(1))
        await meter.async_update()

        print("Serial number:", meter.identity.serial_number)
        print("L1 voltage:", meter.measurements.voltage_l1, "V")
        print("Imported:", meter.measurements.total_import_active_energy, "kWh")
    finally:
        await connection.close()


asyncio.run(main())
```

Behind a gateway the only line that changes is the connection:

```python
from modbus_connection import ModbusTcpParams

connection = ModbusConnection(ModbusTcpParams(host="192.168.1.50", port=502))
```

One `Dsz15dzmod` models one meter, so build one per unit id. That is the normal
deployment rather than the exotic one: the ZGW16WL-IP fronts up to sixteen of
these meters, which reach the consumer as sixteen unit ids on a single
connection.

```python
meters = {unit_id: Dsz15dzmod(connection.for_unit(unit_id)) for unit_id in range(1, 17)}
```

## What it reads

| Component | Space | Contents | Polled |
| --- | --- | --- | --- |
| `measurements` | input (FC04) | Voltages, currents, active power, power factors, totals, energy counters | every `async_update()` |
| `parameters` | holding (FC03/FC16) | Communication address, baud rate, stop bit, pulse mode | once, at setup |
| `identity` | holding (FC03) | Serial number, meter code | once, at setup |

The readings are one component rather than a phase/total/energy split: they
share a space, are always all present, and cannot fail independently. The
settings and the identity are read once at setup — every one of them is
read-only but the communication address, and writing that changes the address
you are talking to.

A poll costs **three requests**: the planner merges fields within 16 registers
of each other, so the small documented holes are read over and only the two
wider gaps split the block (0x0000+36, 0x0034+24, 0x0060+4). The first poll adds
three holding reads for the identity and the settings, and no poll after it
reads them again. This is pinned in `tests/test_read_plan.py`.

`await meter.async_read_raw()` returns every register the meter serves,
undecoded, for a diagnostics dump.

## Checking a real meter

`script/query.py` reads one meter once and prints everything it has, which is
the quickest way to see whether a meter is wired and addressed correctly:

```bash
uv run script/query.py /dev/ttyUSB0 --transport serial --unit 1
uv run script/query.py 192.168.1.50 --unit 1 --framer rtu
```

It prints the read count as well, so the three-request poll above is visible
against real hardware rather than only in the tests.

## Where the register map comes from

Eltako's published *Modbus-RTU protocol specification for DSZ15DZMOD V1.6*,
dated 06/2023. A copy is committed at
[`docs/DSZ15DZMOD-modbus-rtu-v1.6.pdf`](docs/DSZ15DZMOD-modbus-rtu-v1.6.pdf) so
the register definitions can be checked against the datasheet without hunting
for it, and so a later revision of the spec shows up as a visible diff rather
than a silent change. It was downloaded from:

<https://www.eltako.com/fileadmin/downloads/de/_bedienung/Modbus-RTU_protocol_specification_for_DSZ15DZMOD_V1.6_English_version.pdf>

Every value is 4 bytes across two registers, high word in the lower address.
The scaling rules are the spec's own (§3.1 remark 1): everything except power
and power factor is unsigned with two decimals, power factor is signed with
three, and power is signed with none.

## Where the spec is unclear

None of these is resolved here — the model follows the document, and each is
recorded so anyone with a meter on the bench can settle it.

**Active power may be watts, not kW.** The spec gives active power a unit of kW,
signed, and — alone among the measurements — no decimals. That makes the step
1 kW, which is hard to believe from a meter that reports *energy* to two
decimals (10 Wh): the same device would resolve accumulated energy a hundred
thousand times more finely than the power producing it. The likeliest
explanation is that the raw value is watts and the unit column is wrong. The
library does **not** guess: `active_power_l1`, `active_power_l2`,
`active_power_l3` and `total_active_power` hand back the raw signed integer
unscaled, labelled kW as the datasheet labels it. If you measure otherwise,
divide — and please open an issue with what you saw.

**The pulse-mode table contradicts itself.** §3.2 lists "1 reverse active,
2 Total active, 2-4 positive active" for 0x0056, giving code 2 two meanings.
`pulse_mode` is therefore a plain integer and not an enum.

**Baud-rate code 4 is unassigned.** The spec lists 0, 1, 2, 3 and 5. An
unassigned code decodes to `None`.

**The meter code's format is unexplained.** §3.2 gives it as `0000000D` without
saying what `D` denotes, so it is read as a raw unsigned value.

**The worked example in §3.1 remark 2 does not decode.** It says 123456.75
stored at 0x0048 puts 1234 in 0x0048 and 5678 in 0x0049, but that value at two
decimals is 12345675 = 0x00BC614B, which is 188 and 24907 — and it calls the
register "positive active power" while using kWh and the energy address. The
frame in §2.1.2 is the reliable one: `CC 04 08 00 00 01 CD 00 00 01 70 CF D7`
decodes as 4.61 kWh and 3.68 kWh, which is what pins two decimals and
high-word-first. That frame is a test.

**Whether the meter answers for its holes is untested.** The input map has
undocumented gaps that the default read planning merges across. If a meter
refuses those blocks with an illegal-address exception, declaring
`register_ranges` on `Measurements` for the documented blocks confines each read
— at the cost of six requests per poll instead of three.

## Writing

Only the communication address (0x0014) is writable; the spec marks everything
else read only. It is validated against the spec's 1-250 range before anything
goes on the bus, and takes effect immediately — after a successful write the
meter no longer answers on the old unit id.

```python
await meter.parameters.write("communication_address", 42)
```

## License

MIT
