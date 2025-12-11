#!/usr/bin/env python3
# interpreter.py
# CLI interpreter for Variant #9
# Usage:
#  python interpreter.py program.bin memory_dump.csv 100-220
# memory is word-addressable (32-bit words). cmd and data memories are separate.

import argparse
import csv
import math
from src.utils import mask
from pathlib import Path

INSTR_SIZE = 4  # bytes per instruction
def run_binary_bytes(code_bytes, data_mem_size=1<<16, regs_count=32):
    """Альтернативная функция для запуска из байтов (без файла)"""
    # Инициализация состояния
    state = {
        "regs": [0]*regs_count,
        "data_mem": [0]*data_mem_size
    }

    # Выполнение инструкций последовательно
    pc = 0
    code_len = len(code_bytes)
    while pc + INSTR_SIZE <= code_len:
        instr_bytes = code_bytes[pc:pc+INSTR_SIZE]
        cmd_int = int.from_bytes(instr_bytes, "little")
        decode_and_execute_one(cmd_int, state)
        pc += INSTR_SIZE

    return state

def decode_and_execute_one(cmd_int, state):
    """
    cmd_int: 32-bit integer instruction
    state: dict with keys:
       regs: list of int (registers)
       data_mem: list of ints (word-addressable)
    Returns None.
    """
    A = cmd_int & mask(6)
    if A == 29:  # LOAD_CONST
        B = (cmd_int >> 6) & mask(20)   # constant
        C = (cmd_int >> 26) & mask(5)   # dest reg
        state["regs"][C] = B
    elif A == 4:  # READ_MEM
        B = (cmd_int >> 6) & mask(5)    # dest reg
        C = (cmd_int >> 11) & mask(19)  # mem addr
        state["regs"][B] = state["data_mem"][C]
    elif A == 43:  # WRITE_MEM
        B = (cmd_int >> 6) & mask(19)   # mem addr
        C = (cmd_int >> 25) & mask(5)   # source reg
        state["data_mem"][B] = state["regs"][C]
    elif A == 2:  # SQRT
        B = (cmd_int >> 6) & mask(5)    # dest reg
        C = (cmd_int >> 11) & mask(19)  # mem addr
        val = state["data_mem"][C]
        if val < 0:
            raise ValueError("SQRT on negative value")
        # integer sqrt (floor)
        state["regs"][B] = math.isqrt(int(val))
    else:
        raise ValueError(f"Unknown opcode A={A}")

def run_program(bin_path, data_mem_size=1<<16, regs_count=32, dump_csv=None, dump_range=None):
    # read binary
    p = Path(bin_path)
    if not p.exists():
        raise FileNotFoundError(bin_path)
    with open(p, "rb") as f:
        code = f.read()

    # initialize state
    state = {
        "regs": [0]*regs_count,
        "data_mem": [0]*data_mem_size
    }

    # execute instructions sequentially
    pc = 0
    code_len = len(code)
    while pc + INSTR_SIZE <= code_len:
        instr_bytes = code[pc:pc+INSTR_SIZE]
        cmd_int = int.from_bytes(instr_bytes, "little")
        decode_and_execute_one(cmd_int, state)
        pc += INSTR_SIZE

    # dump CSV if requested
    if dump_csv is not None and dump_range is not None:
        start, end = dump_range
        with open(dump_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["address", "value"])
            if start < 0 or end >= data_mem_size:
                raise IndexError("Dump range out of bounds")
            for addr in range(start, end+1):
                writer.writerow([addr, state["data_mem"][addr]])
    return state

def parse_range(s):
    # format "start-end"
    if "-" not in s:
        raise argparse.ArgumentTypeError("Range must be start-end")
    a,b = s.split("-",1)
    return (int(a), int(b))

def main():
    parser = argparse.ArgumentParser(description="Interpreter for UVM Variant #9")
    parser.add_argument("binary", help="Path to binary program")
    parser.add_argument("dump_csv", help="Path to CSV dump file (address,value)")
    parser.add_argument("range", help="Memory dump range start-end (e.g. 100-220)")
    parser.add_argument("--mem-size", type=int, default=1<<16, help="Data memory size (words)")
    parser.add_argument("--regs", type=int, default=32, help="Number of registers")
    args = parser.parse_args()

    dump_range = parse_range(args.range)
    state = run_program(args.binary, data_mem_size=args.mem_size, regs_count=args.regs,
                        dump_csv=args.dump_csv, dump_range=dump_range)
    print("Program executed. Dump written to", args.dump_csv)

if __name__ == "__main__":
    main()
