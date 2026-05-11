from app import create_app

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*args, **kwargs):
        return False

load_dotenv()

app = create_app()

if  __name__== "__main__":
    app.run(debug=True)