from api import app as fastapi_app

# Vercel Python Runtime looks for a top-level `app` variable
app = fastapi_app
