from app import create_app
import os

# Ensure instance directory exists
instance_path = os.path.join(os.path.dirname(__file__), 'instance')
os.makedirs(instance_path, exist_ok=True)

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, use_reloader=True) 