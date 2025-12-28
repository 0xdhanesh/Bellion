# Tool Reference

Complete reference for all binary analysis tools included in this environment.

## Table of Contents

- [file](#file) - File type identification
- [objdump](#objdump) - Object file disassembler
- [readelf](#readelf) - ELF file analyzer
- [strings](#strings) - Extract printable strings
- [nm](#nm) - Symbol table viewer
- [ld](#ld) - GNU linker
- [strace](#strace) - System call tracer
- [ltrace](#ltrace) - Library call tracer
- [gdb](#gdb) - GNU Debugger
- [hexdump](#hexdump) - Hexadecimal viewer
- [od](#od) - Octal/hex dump utility

---

## file

**Purpose**: Determine file type using magic numbers and file signatures.

### Basic Usage

```bash
file mybinary
```

### Common Options

```bash
# Brief output
file -b mybinary

# MIME type
file -i mybinary

# Follow symlinks
file -L mysymlink

# Check multiple files
file *
```

### Example Output

```
mybinary: ELF 64-bit LSB executable, x86-64, version 1 (SYSV), dynamically linked
```

---

## objdump

**Purpose**: Display information from object files and disassemble machine code.

### Basic Usage

```bash
# Disassemble all sections
objdump -d mybinary

# Disassemble specific section
objdump -d -j .text mybinary
```

### Common Options

```bash
# Full disassembly with source (if available)
objdump -S mybinary

# Display all headers
objdump -x mybinary

# Display section headers
objdump -h mybinary

# Display symbol table
objdump -t mybinary

# Intel syntax (instead of AT&T)
objdump -M intel -d mybinary

# Disassemble with addresses
objdump -d --prefix-addresses mybinary
```

### Example: Find Main Function

```bash
objdump -d mybinary | grep -A 20 "<main>:"
```

---

## readelf

**Purpose**: Display information about ELF (Executable and Linkable Format) files.

### Basic Usage

```bash
# Display all information
readelf -a mybinary
```

### Common Options

```bash
# ELF file header
readelf -h mybinary

# Program headers (segments)
readelf -l mybinary

# Section headers
readelf -S mybinary

# Symbol table
readelf -s mybinary

# Dynamic section
readelf -d mybinary

# Relocation entries
readelf -r mybinary

# Notes section
readelf -n mybinary

# Version information
readelf -V mybinary
```

### Example: Check Security Features

```bash
# Check for stack canary
readelf -s mybinary | grep stack_chk

# Check for PIE (Position Independent Executable)
readelf -h mybinary | grep Type

# Check for RELRO
readelf -l mybinary | grep GNU_RELRO
```

---

## strings

**Purpose**: Extract printable character sequences from binary files.

### Basic Usage

```bash
strings mybinary
```

### Common Options

```bash
# Minimum string length (default is 4)
strings -n 8 mybinary

# Show file offset
strings -t x mybinary

# Scan entire file (not just data sections)
strings -a mybinary

# Show encoding
strings -e l mybinary  # little-endian 16-bit
strings -e b mybinary  # big-endian 16-bit
```

### Example: Find Interesting Strings

```bash
# Find URLs
strings mybinary | grep -E "https?://"

# Find potential credentials
strings mybinary | grep -iE "(password|secret|key|token)"

# Find file paths
strings mybinary | grep "^/"

# Find email addresses
strings mybinary | grep -E "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
```

---

## nm

**Purpose**: List symbols from object files.

### Basic Usage

```bash
nm mybinary
```

### Common Options

```bash
# Display dynamic symbols
nm -D mybinary

# Show symbol sizes
nm -S mybinary

# Demangle C++ symbols
nm -C mybinary

# Show only undefined symbols
nm -u mybinary

# Show only external symbols
nm -g mybinary

# Numeric sort by address
nm -n mybinary
```

### Symbol Types

- `T` - Text section (code)
- `D` - Initialized data
- `B` - Uninitialized data (BSS)
- `U` - Undefined (external)
- `W` - Weak symbol

### Example

```bash
# Find main function
nm mybinary | grep " T main"

# List all functions
nm mybinary | grep " T "
```

---

## ld

**Purpose**: GNU linker for combining object files.

### Basic Usage

```bash
ld -o output input.o
```

### Common in Analysis

Typically not used directly for analysis, but understanding linker behavior helps with:
- Understanding symbol resolution
- Analyzing dynamic linking
- Reverse engineering build processes

---

## strace

**Purpose**: Trace system calls and signals.

### Basic Usage

```bash
strace ./mybinary
```

### Common Options

```bash
# Save output to file
strace -o trace.log ./mybinary

# Show timestamps
strace -t ./mybinary
strace -tt ./mybinary  # with microseconds

# Trace specific syscalls
strace -e trace=open,read,write ./mybinary

# Trace file operations
strace -e trace=file ./mybinary

# Trace network operations
strace -e trace=network ./mybinary

# Follow child processes
strace -f ./mybinary

# Count syscalls
strace -c ./mybinary

# Attach to running process
strace -p <PID>
```

### Example: Find File Access

```bash
# See what files are opened
strace -e trace=open,openat ./mybinary 2>&1 | grep -v ENOENT

# Monitor network connections
strace -e trace=connect,socket ./mybinary
```

---

## ltrace

**Purpose**: Trace library calls.

### Basic Usage

```bash
ltrace ./mybinary
```

### Common Options

```bash
# Save to file
ltrace -o trace.log ./mybinary

# Show timestamps
ltrace -t ./mybinary

# Count calls
ltrace -c ./mybinary

# Follow child processes
ltrace -f ./mybinary

# Trace specific functions
ltrace -e malloc,free ./mybinary
```

### Example

```bash
# Find string operations
ltrace -e 'str*' ./mybinary

# Monitor memory allocation
ltrace -e malloc,calloc,realloc,free ./mybinary
```

---

## gdb

**Purpose**: GNU Debugger for debugging and reverse engineering.

### Starting GDB

```bash
# Debug a binary
gdb ./mybinary

# Debug with arguments
gdb --args ./mybinary arg1 arg2

# Attach to running process
gdb -p <PID>
```

### Essential Commands

```gdb
# Execution control
break main              # Set breakpoint at main
break *0x400500         # Set breakpoint at address
run                     # Start execution
continue                # Continue after breakpoint
step                    # Step into functions
next                    # Step over functions
finish                  # Run until function returns

# Examination
info registers          # Show all registers
info breakpoints        # List breakpoints
info functions          # List all functions
info variables          # List variables

# Disassembly
disassemble main        # Disassemble function
disassemble 0x400500    # Disassemble address
set disassembly-flavor intel  # Use Intel syntax

# Memory examination
x/20x $rsp              # Examine 20 hex words at stack pointer
x/s 0x400500            # Examine string at address
x/10i $rip              # Examine 10 instructions at instruction pointer

# Modify execution
set $rax = 0            # Change register value
set {int}0x400500 = 0   # Change memory value

# Other
backtrace               # Show call stack
quit                    # Exit GDB
```

### Example: Basic Debugging Session

```gdb
gdb ./mybinary
(gdb) break main
(gdb) run
(gdb) info registers
(gdb) disassemble
(gdb) x/20x $rsp
(gdb) continue
(gdb) quit
```

---

## hexdump

**Purpose**: Display file contents in hexadecimal format.

### Basic Usage

```bash
# Canonical hex+ASCII display
hexdump -C mybinary
```

### Common Options

```bash
# Canonical format (hex + ASCII)
hexdump -C mybinary

# One-byte octal
hexdump -b mybinary

# Two-byte decimal
hexdump -d mybinary

# Two-byte hex
hexdump -x mybinary

# Custom format
hexdump -e '16/1 "%02x " "\n"' mybinary

# Skip bytes
hexdump -C -s 0x1000 mybinary

# Limit output
hexdump -C -n 256 mybinary
```

### Example: Find Magic Bytes

```bash
# Check ELF magic bytes
hexdump -C mybinary | head -n 1
# Should show: 7f 45 4c 46 (ELF)
```

---

## od

**Purpose**: Octal dump utility (also supports hex and other formats).

### Basic Usage

```bash
od -A x -t x1z -v mybinary
```

### Common Options

```bash
# Hex dump with ASCII
od -A x -t x1z -v mybinary

# Octal dump
od -A x -t o1 mybinary

# Decimal dump
od -A x -t d1 mybinary

# Character dump
od -A x -t c mybinary

# Address format
od -A x    # Hexadecimal addresses
od -A d    # Decimal addresses
od -A o    # Octal addresses
```

### Example

```bash
# Hex dump first 512 bytes
od -A x -t x1z -v -N 512 mybinary
```

---

## Quick Reference Table

| Task | Command |
|------|---------|
| Identify file type | `file mybinary` |
| Disassemble binary | `objdump -d mybinary` |
| View ELF headers | `readelf -h mybinary` |
| Extract strings | `strings mybinary` |
| List symbols | `nm mybinary` |
| Trace syscalls | `strace ./mybinary` |
| Trace library calls | `ltrace ./mybinary` |
| Debug interactively | `gdb ./mybinary` |
| Hex dump | `hexdump -C mybinary` |
| Octal dump | `od -A x -t x1z mybinary` |

---

## Additional Resources

- [GNU Binutils Documentation](https://sourceware.org/binutils/docs/)
- [GDB Documentation](https://sourceware.org/gdb/documentation/)
- [Linux Man Pages](https://man7.org/linux/man-pages/)
- [ELF Format Specification](https://refspecs.linuxfoundation.org/elf/elf.pdf)
