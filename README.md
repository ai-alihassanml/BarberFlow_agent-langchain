# Barber Booking Agent

## Development
 - Install dependencies: `pip install -r requirements.txt` or use your preferred method

### Optional: Local audio / microphone support
This project previously listed `PyAudio` as a direct dependency. `PyAudio` requires the
PortAudio native library and often needs a compiled wheel. Many deployment environments
(for example Vercel serverless) cannot build it, which causes failures like the one
in your screenshot: "Building wheel for pyaudio did not run successfully." To avoid
deployment build failures, `PyAudio` is now an optional extra.

If you need microphone or local audio capture on your development machine, install the
optional `audio` extra or install `PyAudio` manually depending on your platform.

- Windows (recommended):

```powershell
python -m pip install --upgrade pip
python -m pip install pipwin
pipwin install pyaudio
```

- macOS:

```bash
brew install portaudio
pip install pyaudio
- Debian/Ubuntu (Linux):

```bash
sudo apt-get update
sudo apt-get install -y portaudio19-dev python3-dev
pip install pyaudio
```

Or install the optional extra with your package tool if using `pyproject.toml`:

```bash
pip install .[audio]
```

If you're deploying to a serverless provider, prefer sending audio files to the API
and using `SpeechRecognition`'s `AudioFile` or cloud transcription services (Google
Speech-to-Text, OpenAI Whisper, etc.) instead of relying on `PyAudio` at runtime.
# 💈 BarberFlow - AI Appointment Booking Agent

BarberFlow is an intelligent, CLI-based barber appointment booking platform powered by **Google Gemini AI** and **LangGraph**. It allows users to book appointments, check availability, and manage bookings using natural language in a terminal interface.

## 🚀 How It Works (Agent Workflow)

The BarberFlow agent follows a sophisticated workflow to handle user requests:

1.  **User Input**: The user types a message (e.g., "I need a haircut tomorrow at 3 PM") into the CLI.
2.  **Intent Recognition**: The **Gemini AI** model analyzes the input to understand the user's intent (Booking, Inquiry, Cancellation, etc.) and extracts key details like date, time, and service.
3.  **State Management**: **LangGraph** manages the conversation state, tracking collected information (name, service, time) and determining the next step.
4.  **Tool Execution**: The agent uses specialized tools to interact with the **MongoDB** database:
    *   `search_barbers`: Finds barbers based on specialties.
    *   `check_slots`: Calculates real-time availability based on working hours and existing appointments.
    *   `book_appointment`: Creates a new booking record.
5.  **Response Generation**: The AI generates a natural, friendly response confirming the action or asking for missing information.

## 📂 Project Structure

Here is the detailed structure of the BarberFlow project and what each folder contains:

```
barber-booking-agent/
├── agent/                  # 🧠 AI Agent Core
│   ├── graph.py            # Defines the LangGraph workflow and edges
│   ├── nodes.py            # Functions for processing steps (intent, response)
│   ├── states.py           # Defines the agent's memory structure
│   └── tools.py            # Tools for database interaction (search, book)
│
├── config/                 # ⚙️ Configuration
│   ├── database.py         # MongoDB connection and setup
│   └── settings.py         # Environment variables and app settings
│
├── models/                 # 📝 Data Models (Pydantic)
│   ├── appointment.py      # Appointment schema
│   ├── barber.py           # Barber profile and schedule schema
│   ├── service.py          # Service details (price, duration)
│   └── user.py             # User/Customer schema
│
├── services/               # 💼 Business Logic
│   ├── appointment_service.py # Logic for creating/fetching appointments
│   ├── availability_service.py # Complex logic for calculating free slots
│   ├── barber_service.py   # Logic for retrieving barber info
│   └── seed_data.py        # Populates DB with initial sample data
│
├── utils/                  # 🛠️ Utilities
│   ├── cli_formatter.py    # Rich library setup for beautiful terminal UI
│   ├── datetime_utils.py   # Helpers for parsing natural language dates
│   └── validators.py       # Input validation (email, phone)
│
├── main.py                 # 🏁 Entry Point
│                           # Runs the CLI loop and initializes the app
│
├── .env                    # Environment variables (API Keys, DB URI)
└── pyproject.toml          # Project dependencies
```

## 🛠️ Setup & Usage

1.  **Configure Environment**:
    Create a `.env` file and add your keys:
    ```env
    MONGODB_URI=your_mongodb_uri
    GEMINI_API_KEY=your_gemini_api_key
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    # OR
    uv sync
    ```

3.  **Run the Agent**:
    ```bash
    python main.py
    ```
