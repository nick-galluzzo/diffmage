import typer

app = typer.Typer()


@app.command()
def main(debug: bool = typer.Option(False, "--debug", "-d", help="Enable debug mode")):
    if debug:
        try:
            import debugpy

            debugpy.listen(5678)
            print("Waiting for debugger attach on port 5678...")
            print("In VSCode, hit F5 to attach debugger")
            debugpy.wait_for_client()
            print("Debugger attached!")
        except ImportError:
            print(
                "debugpy not installed. Run 'uv pip install debugpy' to enable debugging."
            )
