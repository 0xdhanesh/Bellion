"""Verify the independent REA MCP server inside OSINTDocker."""
import asyncio
import json
from pathlib import Path
import tempfile
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    async with stdio_client(StdioServerParameters(command='rea', args=['mcp'])) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            names = {tool.name for tool in (await session.list_tools()).tools}
            assert 'inspect_artifact' in names, names
            assert 'analyze_javascript_application' in names, names
            with tempfile.TemporaryDirectory(dir='/workspace') as directory:
                target = Path(directory)
                (target / 'package.json').write_text(json.dumps({'name': 'mcp-fixture', 'type': 'module'}))
                (target / 'index.js').write_text('export function greet(name) { return "Hello " + name; }\n')
                result = await session.call_tool('analyze_javascript_application', {'input_path': directory})
                assert not result.isError, result
            print(f'PASS: REA MCP handshake, {len(names)} native tools, static JavaScript analysis')

asyncio.run(main())
