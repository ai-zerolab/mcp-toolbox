import typer

from mcp_toolbox.app import mcp

app = typer.Typer()


@app.command()
def stdio():
    mcp.run(transport="stdio")


@app.command()
def sse(
    host: str = "localhost",
    port: int = 9871,
):
    mcp.settings.host = host
    mcp.settings.port = port
    mcp.run(transport="sse")


if __name__ == "__main__":
    app(["stdio"])
