import speech_recognition as sr
import pyttsx3
import logging
import re
from rich.console import Console

console = Console()
logger = logging.getLogger(__name__)


class VoiceService:
    def __init__(self):
        # Speech recognition is generally available as long as the library imports
        self.recognizer = sr.Recognizer()

        # TTS engine (may fail on some systems)
        self.engine = None
        self.is_available = False  # Backwards-compatible flag for TTS availability

        try:
            self.engine = pyttsx3.init()
            # Configure voice properties (optional)
            voices = self.engine.getProperty("voices")
            # Try to find a good English voice
            for voice in voices:
                if "english" in voice.name.lower():
                    self.engine.setProperty("voice", voice.id)
                    break

            # Slightly slower than default for clearer pronunciation
            self.engine.setProperty("rate", 170)
            self.is_available = True
        except Exception as e:
            logger.error(f"Failed to initialize TTS engine: {e}")
            console.print(f"[yellow]Warning: Voice output not available ({e})[/yellow]")

    def listen(self) -> str:
        """Listen to microphone and convert speech to text.

        Returns empty string if failed or silence. This method is
        independent from TTS availability so that recognition still
        works even when speaking is not possible.
        """

        try:
            with sr.Microphone() as source:
                console.print("[cyan]Listening... (Speak now)[/cyan]")
                # Adjust for ambient noise (slightly longer for stability)
                self.recognizer.adjust_for_ambient_noise(source, duration=0.8)

                # timeout: max seconds waiting for speech to start
                # phrase_time_limit: max length of the utterance
                audio = self.recognizer.listen(source, timeout=7, phrase_time_limit=12)

                console.print("[dim]Processing speech...[/dim]")
                text = self.recognizer.recognize_google(audio)
                text = text.strip()
                if not text:
                    console.print("[yellow]Heard silence.[/yellow]")
                    return ""

                console.print(f"[green]You said:[/green] {text}")
                return text
        except sr.WaitTimeoutError:
            console.print("[yellow]No speech detected.[/yellow]")
            return ""
        except sr.UnknownValueError:
            console.print("[yellow]Could not understand audio.[/yellow]")
            return ""
        except sr.RequestError as e:
            console.print(f"[red]Speech recognition service error: {e}[/red]")
            logger.error(f"Speech recognition service error: {e}")
            return ""
        except Exception as e:
            logger.error(f"Microphone error: {e}")
            console.print("[red]Microphone error occurred. Please check your audio device.[/red]")
            return ""

    def speak(self, text: str):
        """Convert text to speech.

        Cleans up markdown and rich formatting so the spoken
        response closely matches the printed one.
        """

        if not self.is_available or not self.engine:
            return

        try:
            if not text:
                return

            # Strip rich-style tags like [bold], [yellow] etc.
            clean_text = re.sub(r"\[[^\]]*\]", "", text)

            # Remove common markdown characters that sound strange when read
            for ch in ["*", "#", "`", "_", "|", ":"]:
                clean_text = clean_text.replace(ch, "")

            # Normalize whitespace
            clean_text = re.sub(r"\s+", " ", clean_text).strip()

            if not clean_text:
                return

            self.engine.say(clean_text)
            self.engine.runAndWait()
        except Exception as e:
            logger.error(f"TTS error: {e}")

# Global instance
voice_service = VoiceService()
