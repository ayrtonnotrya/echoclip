import typer
from rich.console import Console
from rich.prompt import Prompt
from echoclip.config import config
from echoclip.service import install_service, start_service
from echoclip.assets import generate_system_sounds
from echoclip.input_handler import input_listener
from echoclip.logger import logger

app = typer.Typer()
console = Console()

@app.command()
def init():
    """Initialize EchoClip configuration and services."""
    console.print("[bold green]EchoClip Initialization[/bold green]")
    
    # 1. API Keys
    current_keys = config.gemini_api_keys
    if not current_keys:
        keys_str = Prompt.ask("Enter Gemini API Keys (separated by |)")
        if keys_str:
            config.gemini_api_keys = [k.strip() for k in keys_str.split("|")]
            config.save()
            console.print("API keys saved.")
    else:
        console.print(f"Found {len(current_keys)} API keys.")

    # 2. Generate Assets
    console.print("Generating system sounds...")
    try:
        generate_system_sounds()
        console.print("[green]Assets generated.[/green]")
    except Exception as e:
        console.print(f"[red]Failed to generate assets: {e}[/red]")

    # 3. Install Service
    if typer.confirm("Install systemd user service?"):
        try:
            install_service()
            console.print("[green]Service installed and enabled.[/green]")
        except Exception as e:
            console.print(f"[red]Failed to install service: {e}[/red]")

@app.command()
def start():
    """Start the EchoClip listener."""
    logger.info("Starting EchoClip...")
    try:
        input_listener.start()
    except KeyboardInterrupt:
        logger.info("Stopping...")

if __name__ == "__main__":
    app()
