from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.markdown import Markdown
from typing import List
from models.appointment import Appointment
from models.barber import Barber
from utils.datetime_utils import format_datetime_friendly

console = Console()

def print_welcome():
    """Display welcome screen with logo."""
    title = Text("💈 BarberFlow 💈", style="bold magenta", justify="center")
    subtitle = Text("AI-Powered Appointment Booking Assistant", style="italic cyan", justify="center")
    
    panel = Panel(
        Text.assemble(title, "\n", subtitle),
        border_style="magenta",
        padding=(1, 2)
    )
    console.print(panel)
    console.print("[dim]Type '/help' for commands or just chat naturally to book![/dim]\n")

def print_appointment_table(appointments: List[Appointment]):
    """Display appointments in a formatted table."""
    if not appointments:
        console.print("[yellow]No appointments found.[/yellow]")
        return

    table = Table(title="Your Appointments", show_header=True, header_style="bold magenta")
    table.add_column("Date & Time", style="cyan")
    table.add_column("Service", style="green")
    table.add_column("Barber", style="blue")
    table.add_column("Status", style="white")

    for appt in appointments:
        status_style = "green" if appt.status == "confirmed" else "red"
        table.add_row(
            format_datetime_friendly(appt.appointment_datetime),
            appt.service_type,
            appt.barber_name,
            f"[{status_style}]{appt.status}[/{status_style}]"
        )

    console.print(table)

def print_barbers_list(barbers: List[Barber]):
    """Display barbers with their info."""
    if not barbers:
        console.print("[yellow]No barbers found.[/yellow]")
        return

    table = Table(title="Available Barbers", show_header=True, header_style="bold blue")
    table.add_column("Name", style="bold white")
    table.add_column("Specialties", style="cyan")
    table.add_column("Rating", style="yellow")

    for barber in barbers:
        specialties = ", ".join(barber.specialties)
        table.add_row(
            barber.name,
            specialties,
            f"⭐ {barber.rating}"
        )

    console.print(table)

def print_agent_message(message: str):
    """Display AI agent message with formatting."""
    console.print(f"\n[bold magenta]Agent:[/bold magenta] {message}")

def print_user_prompt():
    """Display user input prompt."""
    return console.input("\n[bold green]You:[/bold green] ")

def print_error(message: str):
    """Display error message."""
    console.print(f"[bold red]Error:[/bold red] {message}")

def print_success(message: str):
    """Display success message."""
    console.print(f"[bold green]Success:[/bold green] {message}")
