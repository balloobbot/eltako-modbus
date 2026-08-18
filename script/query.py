#!/usr/bin/env python3

"""Query an Eltako meter and print every value.

Reads one meter once and dumps it to the terminal — the quickest way to check a
real meter with no application around it. Which model it is comes from the
meter itself unless ``--model`` says otherwise.

::

    uv run script/query.py /dev/ttyUSB0 --transport serial --unit 1
    uv run script/query.py 192.168.1.50 --unit 1 --framer rtu
    uv run script/query.py 192.168.1.50 --unit 1 --model dsz15dzmod
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

from eltako_modbus import MODELS, EltakoMeter, async_detect_meter

# Every model by the name --model takes, keyed off the spec's own model codes.
BY_NAME = {mode.name.lower(): build for mode, build in MODELS.items()}

# The meter is RS-485 RTU; over TCP it is reached through a gateway, which
# presents it either transparently (rtu) or as native Modbus TCP (socket). The
# first pair is what --transport defaults to.
CONNECTIONS = (("tcp", "rtu"), ("tcp", "socket"), ("serial", "rtu"))


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    add_connection_args(parser, connections=CONNECTIONS)
    parser.add_argument("--unit", type=int, default=1, help="Modbus unit id")
    parser.add_argument(
        "--model",
        choices=sorted(BY_NAME),
        help="skip detection and read the meter as this model",
    )
    args = parser.parse_args()

    try:
        connection = await connect_from_args(args)
    except ModbusError as err:
        print(f"Could not connect: {err}")
        return 1

    counting = CountingUnit(connection.for_unit(args.unit))
    meter: EltakoMeter
    try:
        if args.model:
            meter = BY_NAME[args.model](counting)
        else:
            meter = await async_detect_meter(counting)
        await meter.async_update()
    except ModbusError as err:
        print(f"Could not read the meter: {err}")
        return 1
    except ValueError as err:  # a meter mode no model of the spec has
        print(f"Could not identify the meter: {err}")
        return 1
    finally:
        await connection.close()

    print(f"{meter.manufacturer} {meter.model}")
    print_component(meter.identity, title="Identity")
    print_component(meter.parameters, title="Settings")
    print_component(meter.measurements, title="Measurements")
    print(f"\n{counting.reads} Modbus reads")
    return 0


raise SystemExit(asyncio.run(main()))
