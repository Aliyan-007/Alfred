import asyncio
import shutil

from mcp import (
    ClientSession,
    StdioServerParameters,
)

from mcp.client.stdio import stdio_client


async def main():
    npx = shutil.which("npx")

    if not npx:
        raise RuntimeError(
            "npx was not found on PATH."
        )

    server_params = StdioServerParameters(
        command=npx,
        args=[
            "-y",
            "brave-mcp@latest",
            "--autoConnect",
        ],
    )

    async with stdio_client(
        server_params
    ) as (
        read_stream,
        write_stream,
    ):

        async with ClientSession(
            read_stream,
            write_stream,
        ) as session:

            await session.initialize()

            result = await session.list_tools()

            print(
                f"\nFound {len(result.tools)} Brave tools:\n"
            )

            for tool in result.tools:

                print("=" * 70)

                print(
                    f"NAME: {tool.name}"
                )

                print(
                    f"DESCRIPTION: "
                    f"{tool.description or ''}"
                )

                schema = getattr(
                    tool,
                    "input_schema",
                    None,
                )

                if schema:
                    print("SCHEMA:")
                    print(schema)

                print()


if __name__ == "__main__":
    asyncio.run(main())