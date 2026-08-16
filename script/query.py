#!/usr/bin/env python3

"""Query an Eltako DSZ15DZMOD and print every value.

Reads one meter once and dumps it to the terminal — the quickest way to check a
real meter with no application around it.

::

    uv run script/query.py /dev/ttyUSB0 --transport serial --unit 1
    uv run script/query.py 192.168.1.50 --unit 1 --framer rtu
"""

from __future__ import annotations

import argparse
import asyncio

from modbus_connection import ModbusError
from modbus_connection.cli_helper import (
    CountingUnit,
    add_connection_args,
    connect_from_args,
    print_component,
)

from eltako_modbus import Dsz15dzmod

# The meter is RS-485 RTU; over TCP it is reached through a gateway, which
# presents it either transparently (rtu) or as native Modbus TCP (socket). The
# first pair is what --transport defaults to.
CONNECTIONS = (("tcp", "rtu"), ("tcp", "socket"), ("serial", "rtu"))


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    add_connection_args(parser, connections=CONNECTIONS)
    parser.add_argument("--unit", type=int, default=1, help="Modbus unit id")
    args = parser.parse_args()

    try:
        connection = await connect_from_args(args)
    except ModbusError as err:
        print(f"Could not connect: {err}")
        return 1

    counting = CountingUnit(connection.for_unit(args.unit))
    meter = Dsz15dzmod(counting)
    try:
        await meter.async_update()
    except ModbusError as err:
        print(f"Could not read the meter: {err}")
        return 1
    finally:
        await connection.close()

    print_component(meter.identity, title="Identity")
    print_component(meter.parameters, title="Settings")
    print_component(meter.measurements, title="Measurements")
    print(f"\n{counting.reads} Modbus reads")
    return 0


raise SystemExit(asyncio.run(main()))
