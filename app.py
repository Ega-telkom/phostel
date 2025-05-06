from app import create_app
from flask import current_app

app = create_app()

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5500, debug=False, use_reloader=False)

# if __name__ == '__main__':
#     app.run(debug=True, port=5500)