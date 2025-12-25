from app import create_app, db

import os

env_name = os.environ.get('FLASK_ENV', 'development')
app = create_app(env_name)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    # Debug only active if FLASK_ENV is 'development'
    debug_mode = (env_name == 'development')
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)
