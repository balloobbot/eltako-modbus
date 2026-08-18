# eltako-modbus

Read an **Eltako energy meter** over Modbus.

Eltako publishes two Modbus documents, and this library models both: the
DSZ15DZMOD's own datasheet, and the *Modbus-RTU protocol specification V3.7.4*
that covers six further meters. All seven are DIN-rail kWh meters that speak
Modbus RTU on RS-485.

| Class | Meter | Phases | Counts | Notes |
| --- | --- | --- | --- | --- |
| `Dsz15dzmod` | DSZ15DZMOD | three | both directions | its own datasheet |
| `Dsz16d` | DSZ16D | three | import | also sold as DSZ16DE |
| `Dsz16dz` | DSZ16DZ | three | both directions | also sold as DSZ16DZE |
| `Dsz16wd` | DSZ16WD | three | import | through current transformers |
| `Dsz16wdz` | DSZ16WDZ | three | both directions | through current transformers |
| `Wsz16d` | WSZ16D | one | import | also sold as WSZ16DE |
| `Wsz16dz` | WSZ16DZ | one | both directions | also sold as WSZ16DZE |

The six DSZ16/WSZ16 meters live in `eltako_modbus.series16` and share one
register map: per-phase voltage, current, active, apparent and reactive power,
power factor and cosφ, the totals, frequency, and energy counters per tariff
and per phase. The DSZ15DZMOD is modelled apart from them, because its own
datasheet disagrees with V3.7.4 — see [Where the two specs
disagree](#where-the-two-specs-disagree).

This is a device library built on
[modbus-connection](https://github.com/balloob/modbus-connection). It takes a
`ModbusUnit` and never opens a connection of its own — the consumer owns the
link, and so chooses the transport.

The meters speak Modbus RTU on RS-485, at 9600 baud, 8 data bits, 1 stop bit
and no parity unless they have been reconfigured. Reach one over a serial
adapter with those line settings, or over TCP through a gateway such as
Eltako's ZGW16WL-IP, which fronts up to sixteen meters. Nothing in this library
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

from eltako_modbus import Dsz16dz


async def main() -> None:
    connection = ModbusConnection(ModbusSerialParams(device="/dev/ttyUSB0"))
    try:
        meter = Dsz16dz(connection.for_unit(1))
        await meter.async_update()

        print("Serial number:", meter.identity.serial_number)
        print("L1 voltage:", meter.measurements.voltage_l1, "V")
        print("Imported:", meter.measurements.total_import_active_energy, "kWh")
        print("Exported:", meter.measurements.total_export_active_energy, "kWh")
    finally:
        await connection.close()


asyncio.run(main())
```

Behind a gateway the only line that changes is the connection:

```python
from modbus_connection import ModbusTcpParams

connection = ModbusConnection(ModbusTcpParams(host="192.168.1.50", port=502))
```

One meter object models one meter, so build one per unit id. That is the normal
deployment rather than the exotic one: the ZGW16WL-IP fronts up to sixteen
meters, which reach the consumer as sixteen unit ids on a single connection.

```python
meters = {unit_id: Dsz16dz(connection.for_unit(unit_id)) for unit_id in range(1, 17)}
```

### Asking the meter what it is

Every meter of the V3.7.4 spec — the DSZ15DZMOD included — reports its model in
register 0xFC0C, so a consumer that does not know which one is on the bus can
ask:

```python
from eltako_modbus import async_detect_meter

meter = await async_detect_meter(connection.for_unit(1))
print(meter.model)  # e.g. "WSZ16DZ"
await meter.async_update()
```

Detection costs one two-register read, and raises `ValueError` if the meter
reports a code the spec assigns to no model.

## What it reads

Every model exposes the same four sub-systems:

| Component | Space | Contents | Polled |
| --- | --- | --- | --- |
| `measurements` | input (FC04) | Voltages, currents, power, power factors, frequency, energy counters | every `async_update()` |
| `parameters` | holding (FC03/FC16) | Communication settings, S0 pulse output, tariff selection, CT ratio | once, at setup |
| `identity` | holding (FC03) | Serial number, manufacturing code, meter mode, software version | once, at setup |
| `resets` | holding (FC16) | The counter resets — written, never read | never |

The readings are one component rather than a phase/total/energy split: they
share a space, are always all present, and cannot fail independently. The
settings and the identity are read once at setup.

Each model declares only the points its own Support column lists, so a poll
never asks for a register the meter does not serve. A three-phase DSZ16 poll
costs **two requests** — the map's holes are all narrower than the planner's
16-register `max_gap`, so only the 125-register ceiling on one request splits
the block — and a single-phase WSZ16 poll costs three. The DSZ15DZMOD's costs
three. The first poll adds the holding reads for the identity and the settings,
and no poll after it reads them again. All of this is pinned in
`tests/test_read_plan.py` and `tests/test_series16_read_plan.py`.

The settings a model lacks are scattered through the block rather than grouped,
so `parameters` and `resets` are one layout narrowed per model with
`restrict_fields`: a setting the meter does not have reads as `None` and cannot
be written. That costs a round trip or two at setup, which is where it does not
matter.

`await meter.async_read_raw()` returns every register the meter is read from,
undecoded, for a diagnostics dump.

## Checking a real meter

`script/query.py` reads one meter once and prints everything it has, which is
the quickest way to see whether a meter is wired and addressed correctly:

```bash
uv run script/query.py /dev/ttyUSB0 --transport serial --unit 1
uv run script/query.py 192.168.1.50 --unit 1 --framer rtu
uv run script/query.py 192.168.1.50 --unit 1 --model wsz16dz
```

It detects the model unless `--model` names one, and prints the read count as
well, so the poll cost above is visible against real hardware rather than only
in the tests.

## Writing

The DSZ16 and WSZ16 meters take writes to every setting `parameters` declares —
communication format and address, baud rate, data format, S0 pulse widths and
constants, tariff selection, CT ratio and measurement direction — and to the
counter resets. Values are validated against the spec's ranges before anything
goes on the bus.

```python
from eltako_modbus.series16 import BaudRate, TariffSelection

await meter.parameters.write("baud_rate", BaudRate.BPS_19200)
await meter.parameters.write("tariff_selection", TariffSelection.TARIFF_2)
await meter.resets.write("total_import_active_energy", 1)  # zero the counter
```

Note that the spec makes the E2/E3/E4 control wiring take priority over
`tariff_selection`: a tariff chosen over Modbus holds only while those
terminals stay disconnected.

On the DSZ15DZMOD only the communication address (0x0014) is writable; its
datasheet marks everything else read only. On every model a successful address
write takes effect immediately — the meter no longer answers on the old unit
id, so build a new unit at the new one.

```python
await meter.parameters.write("communication_address", 42)
```

## Where the register maps come from

Both documents are committed under `docs/`, so the register definitions can be
checked against the datasheet without hunting for it, and so a later revision
shows up as a visible diff rather than a silent change.

- [`docs/DSZ15DZMOD-modbus-rtu-v1.6.pdf`](docs/DSZ15DZMOD-modbus-rtu-v1.6.pdf)
  — *Modbus-RTU protocol specification for DSZ15DZMOD V1.6*, 06/2023, from
  <https://www.eltako.com/fileadmin/downloads/de/_bedienung/Modbus-RTU_protocol_specification_for_DSZ15DZMOD_V1.6_English_version.pdf>
- [`docs/Eltako-Modbus-RTU-Specification-v3.7.4.pdf`](docs/Eltako-Modbus-RTU-Specification-v3.7.4.pdf)
  — *Modbus-RTU protocol specification V3.7.4*, 05/2026, from
  <https://www.eltako.com/fileadmin/downloads/de/Technische_Daten/Eltako_Modbus-RTU_Specification_V3.7.4.pdf>

In both, every value is 4 bytes across two registers, high word in the lower
address. The scaling rules are the same words in both: everything except power
and power factor is unsigned with two decimals, power factor is signed with
three, and power is signed with none. V3.7.4 adds that the DSZ16WD and DSZ16WDZ
keep only one decimal of energy, which is Note 1 there and `CT_ENERGY_SCALE`
here.

## Where the two specs disagree

Both documents describe the DSZ15DZMOD, and they contradict each other on three
points. Each model follows **its own** document; nothing is silently
reconciled.

**The unit of power.** The DSZ15DZMOD datasheet says kW; V3.7.4 says W, for
that meter as well as the other six. The decoded number is the same raw signed
integer either way — only the unit label differs — so `Dsz15dzmod` still labels
it kW as its datasheet does, and the DSZ16/WSZ16 models label it W. V3.7.4 is
the likelier of the two (see the next section), but changing the DSZ15DZMOD
would change what a consumer's kW reading means by a factor of a thousand, on
the strength of a document that is not that meter's own. If you have one on the
bench, measure it and open an issue.

**The baud-rate codes.** The DSZ15DZMOD datasheet numbers them 0=2400, 1=4800,
2=9600, 3=19200, 5=1200; V3.7.4 numbers them 0=300 through 5=9600 up to
0x0A=115200. The two tables agree on nothing but the default speed. There are
therefore two `BaudRate` enums: `eltako_modbus.BaudRate` and
`eltako_modbus.series16.BaudRate`.

**The address range.** The DSZ15DZMOD datasheet allows 1-250, V3.7.4 allows
1-247. Each model validates writes against its own.

## Where the specs are unclear

None of these is resolved here — the model follows the document, and each is
recorded so anyone with a meter on the bench can settle it.

**Active power may be watts, not kW (DSZ15DZMOD).** Its datasheet gives active
power a unit of kW, signed, and — alone among the measurements — no decimals.
That makes the step 1 kW, which is hard to believe from a meter that reports
*energy* to two decimals (10 Wh): the same device would resolve accumulated
energy a hundred thousand times more finely than the power producing it. V3.7.4
gives the same register a unit of W, which is what one would expect. The
library does **not** guess: `active_power_l1`, `active_power_l2`,
`active_power_l3` and `total_active_power` hand back the raw signed integer
unscaled, labelled kW as that datasheet labels it. If you measure otherwise,
divide — and please open an issue with what you saw.

**Apparent and reactive power are modelled by the power rule.** V3.7.4's
Remarks say "power is a signed number without decimal" and name no other
quantity, but they exempt only "power and power factor" from the two-decimal
default. Apparent power in VA and reactive power in var are read as signed
integers here, which the unit column implies and nothing in the document
states.

**The frequency's data-format column says two digits.** V3.7.4 gives frequency
`000000XX`, which leaves no room for a mains frequency, while its Remarks give
every unsigned value two decimals. `frequency` follows the Remarks.

**The selected tariff is read raw.** V3.7.4's table for 0x0098 says "1 =
Tariff1", but the Remarks' two-decimal rule would make that 100. The more
specific statement wins: `selected_tariff` decodes 1-4.

**The pulse-mode table contradicts itself (DSZ15DZMOD).** Its §3.2 lists "1
reverse active, 2 Total active, 2-4 positive active" for 0x0056, giving code 2
two meanings. `pulse_mode` is therefore a plain integer and not an enum. In
V3.7.4 that same register is the S0 import pulse width in ms, which the
DSZ15DZMOD does not have at all.

**Baud-rate code 4 is unassigned (DSZ15DZMOD).** Its datasheet lists 0, 1, 2, 3
and 5. An unassigned code decodes to `None`.

**The manufacturing code's format is unexplained.** Both documents give it as
`0000000D` without saying what `D` denotes, so it is read as a raw unsigned
value. The software version's `00NNNNNN` is unexplained the same way.

**Writing with FC06 targets an odd address.** V3.7.4's §2.3.2 changes the meter
address with `CC 06 00 15 00 2A 58 0C` — register 0x0015, the low word of the
32-bit value at 0x0014 — while its §2.4 says an odd register address is an
illegal data address. This library writes 32-bit values whole, with FC16, which
is what §2.3.1 shows and what the DSZ16xx and WSZ16xx meters support.

**A meter switched to float encoding is not modelled.** Parameter 0x001E
selects integer or float measurements. V3.7.4 documents no word order for the
float encoding, so only the integer default is decoded; the setting is exposed
so a consumer can at least see that a meter is in the other mode.

**The worked example in the DSZ15DZMOD's §3.1 remark 2 does not decode.** It
says 123456.75 stored at 0x0048 puts 1234 in 0x0048 and 5678 in 0x0049, but
that value at two decimals is 12345675 = 0x00BC614B, which is 188 and 24907 —
and it calls the register "positive active power" while using kWh and the
energy address. The frames in §2.1.2 and V3.7.4's §2.2.2 are the reliable ones:
`CC 04 08 00 00 01 CD 00 00 01 70 CF D7` decodes as 4.61 kWh and 3.68 kWh,
which is what pins two decimals and high-word-first. That frame is a test.

**Whether a meter answers for its holes is untested.** The input maps have
undocumented gaps that the default read planning merges across. If a meter
refuses those blocks with an illegal-address exception, declaring
`register_ranges` on its measurement layout for the documented blocks confines
each read — at the cost of many more requests per poll.

## License

MIT
