# Usage Guide

This guide provides detailed instructions for using the Ubuntu Binary Analysis Environment.

## Building the Docker Image

### Basic Build

```bash
cd /path/to/ubuntu-64
docker build -t ubuntu-binary-analysis:latest .
```

### Build with Custom Tag

```bash
docker build -t my-analysis-env:v1.0 .
```

### Build with No Cache

If you need to rebuild from scratch:

```bash
docker build --no-cache -t ubuntu-binary-analysis:latest .
```

## Running the Container

### Interactive Shell

Start an interactive bash session:

```bash
docker run --rm -it ubuntu-binary-analysis:latest
```

**Flags explained:**
- `--rm` - Automatically remove container when it exits
- `-it` - Interactive terminal

### Mounting Files for Analysis

#### Mount Current Directory

```bash
docker run --rm -it -v $(pwd):/analysis ubuntu-binary-analysis:latest
```

#### Mount Specific Directory

```bash
docker run --rm -it -v /path/to/binaries:/analysis ubuntu-binary-analysis:latest
```

#### Mount Multiple Directories

```bash
docker run --rm -it \
  -v /path/to/binaries:/analysis \
  -v /path/to/output:/output \
  ubuntu-binary-analysis:latest
```

### Running One-Off Commands

Execute a single command without entering the shell:

```bash
docker run --rm -v $(pwd):/analysis ubuntu-binary-analysis:latest file /analysis/mybinary
```

## Common Analysis Workflows

### Workflow 1: Static Binary Analysis

```bash
# Start container with your binary mounted
docker run --rm -it -v $(pwd):/analysis ubuntu-binary-analysis:latest

# Inside container:
cd /analysis

# Identify file type
file mybinary

# Check if stripped or not
file mybinary | grep -q "not stripped" && echo "Has symbols" || echo "Stripped"

# Display ELF header
readelf -h mybinary

# List section headers
readelf -S mybinary

# Display program headers
readelf -l mybinary

# Show symbol table (if not stripped)
readelf -s mybinary

# Disassemble main function
objdump -d mybinary | grep -A 50 "<main>:"

# Extract strings (minimum 8 characters)
strings -n 8 mybinary

# Find interesting strings
strings mybinary | grep -E "(password|key|secret|token|api)"
```

### Workflow 2: Dynamic Analysis

```bash
# Start container
docker run --rm -it -v $(pwd):/analysis ubuntu-binary-analysis:latest

# Trace system calls
strace -o /analysis/syscalls.log /analysis/mybinary

# Trace with timestamps
strace -tt /analysis/mybinary

# Trace specific syscalls
strace -e trace=open,read,write /analysis/mybinary

# Trace library calls
ltrace /analysis/mybinary

# Count syscalls
strace -c /analysis/mybinary
```

### Workflow 3: Debugging with GDB

```bash
docker run --rm -it -v $(pwd):/analysis ubuntu-binary-analysis:latest

# Start GDB
gdb /analysis/mybinary

# Common GDB commands:
# (gdb) break main          # Set breakpoint at main
# (gdb) run                 # Start execution
# (gdb) info registers      # Show register values
# (gdb) disassemble main    # Disassemble main function
# (gdb) x/20x $rsp          # Examine stack
# (gdb) continue            # Continue execution
# (gdb) quit                # Exit GDB
```

### Workflow 4: Hex Analysis

```bash
docker run --rm -it -v $(pwd):/analysis ubuntu-binary-analysis:latest

# Canonical hex dump
hexdump -C /analysis/mybinary | head -n 50

# Hex dump with ASCII
od -A x -t x1z -v /analysis/mybinary | head -n 50

# Search for specific bytes
hexdump -C /analysis/mybinary | grep "deadbeef"
```

## Advanced Usage

### Persistent Container

Create a named container that persists:

```bash
# Create and start
docker run -it --name my-analysis -v $(pwd):/analysis ubuntu-binary-analysis:latest

# Exit container (Ctrl+D or 'exit')

# Restart later
docker start -ai my-analysis

# Remove when done
docker rm my-analysis
```

### Custom Entrypoint

Override the default shell:

```bash
docker run --rm -it --entrypoint /bin/sh ubuntu-binary-analysis:latest
```

### Resource Limits

Limit CPU and memory usage:

```bash
docker run --rm -it \
  --cpus="2" \
  --memory="1g" \
  -v $(pwd):/analysis \
  ubuntu-binary-analysis:latest
```

### Network Analysis

If your binary makes network connections:

```bash
# Run with network access
docker run --rm -it --network host -v $(pwd):/analysis ubuntu-binary-analysis:latest

# Or isolate completely
docker run --rm -it --network none -v $(pwd):/analysis ubuntu-binary-analysis:latest
```

## Tips and Best Practices

### Performance on Apple Silicon

- The container runs x86_64 binaries through Rosetta 2 emulation
- Performance is excellent for most analysis tasks
- CPU-intensive operations may be slower than native execution

### File Permissions

Files created inside the container may have different ownership:

```bash
# Fix permissions after analysis
sudo chown -R $(whoami):$(whoami) ./output
```

### Saving Analysis Results

Always mount an output directory to save results:

```bash
docker run --rm -it \
  -v $(pwd)/binaries:/analysis \
  -v $(pwd)/results:/output \
  ubuntu-binary-analysis:latest

# Inside container, save to /output
strace -o /output/trace.log /analysis/mybinary
```

### Shell Aliases

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
alias binanalysis='docker run --rm -it -v $(pwd):/analysis ubuntu-binary-analysis:latest'
```

Then simply run:

```bash
binanalysis
```

## Troubleshooting

### Container Won't Start

```bash
# Check Docker is running
docker ps

# View Docker logs
docker logs <container-id>

# Rebuild image
docker build --no-cache -t ubuntu-binary-analysis:latest .
```

### Permission Denied Errors

```bash
# Ensure binary is executable
chmod +x mybinary

# Or run with sudo inside container
docker run --rm -it --user root -v $(pwd):/analysis ubuntu-binary-analysis:latest
```

### Out of Disk Space

```bash
# Clean up unused images
docker system prune -a

# Remove specific image
docker rmi ubuntu-binary-analysis:latest
```

## Next Steps

- See [TOOLS.md](TOOLS.md) for detailed tool reference
- Check [README.md](../README.md) for quick examples
- Read [CONTRIBUTING.md](../CONTRIBUTING.md) to contribute
