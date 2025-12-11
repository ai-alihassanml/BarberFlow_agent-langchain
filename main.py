import asyncio
import os
from dotenv import load_dotenv
from rich.console import Console
from rich.prompt import Prompt, Confirm
# Test Deployment

# Load env before imports
load_dotenv()

from config.database import connect_to_mongo, close_mongo_connection
from services.seed_data import initialize_database
from agent.graph import agent
from utils.cli_formatter import (
    print_welcome, 
    print_agent_message, 
    print_error,
    print_appointment_table,
    print_barbers_list
)
from services.appointment_service import get_appointments_by_email
from services.barber_service import get_all_barbers
from services.voice_service import voice_service
from langchain_core.messages import HumanMessage

console = Console()

async def main():
    # Startup
    try:
        await connect_to_mongo()
        await initialize_database()
    except Exception as e:
        print_error(f"Failed to start application: {e}")
        return

    print_welcome()

    # Configure logging to file
    import logging
    logging.basicConfig(filename='app.log', level=logging.ERROR, 
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Voice Mode Selection
    use_voice = Confirm.ask("Do you want to enable [bold cyan]Voice Mode[/bold cyan]?", default=False)
    if use_voice:
        console.print("[green]Voice Mode Enabled! 🎙️[/green]")
        console.print("Speak clearly into your microphone. You can still type commands.")

        # Phone-call style: assistant speaks first when possible
        intro_message = "Voice mode is enabled. You can talk to me like a phone call. How can I help you today?"
        print_agent_message(intro_message)
        if voice_service.is_available:
            voice_service.speak(intro_message)

    # Chat loop
    chat_history = []
    
    while True:
        try:
            user_input = ""
            
            # Voice Input
            if use_voice:
                # Primary path: speak & listen like a phone call
                user_input = voice_service.listen()
                if not user_input:
                    # Fallback to text if voice fails or is silent
                    user_input = Prompt.ask("\n[bold green]You (Type or Speak)[/bold green]")
            else:
                user_input = Prompt.ask("\n[bold green]You[/bold green]")
            
            if not user_input:
                continue

            if user_input.lower() in ['/exit', '/quit', 'exit', 'quit']:
                console.print("[yellow]Goodbye! See you soon! 👋[/yellow]")
                if use_voice:
                    voice_service.speak("Goodbye! See you soon!")
                break
                
            if user_input.lower() == '/help':
                console.print("\n[bold cyan]Available Commands:[/bold cyan]")
                console.print("• /appointments - View your appointments")
                console.print("• /barbers - List available barbers")
                console.print("• /exit - Quit the application")
                continue

            if user_input.lower() == '/barbers':
                barbers = await get_all_barbers()
                print_barbers_list(barbers)
                continue
                
            # Process with Agent
            inputs = {
                "messages": chat_history + [HumanMessage(content=user_input)],
            }
            
            response = await agent.ainvoke(inputs)
            
            # Get AI response
            ai_message = response["messages"][-1].content
            print_agent_message(ai_message)
            
            # Voice Output (speak responses whenever TTS is available)
            if use_voice and voice_service.is_available:
                voice_service.speak(ai_message)
            
            # Update history
            chat_history.append(HumanMessage(content=user_input))
            chat_history.append(response["messages"][-1])
            
        except KeyboardInterrupt:
            console.print("\n[yellow]Goodbye![/yellow]")
            break
        except Exception as e:
            logging.error("An error occurred", exc_info=True)
            print_error(f"An error occurred: {e}. See app.log for details.")

    # Shutdown
    await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(main())
