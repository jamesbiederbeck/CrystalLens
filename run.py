from app import create_app

app = create_app()

if __name__ == '__main__':
    # Keep the legacy development server local and its interactive debugger off.
    app.run(host='127.0.0.1', port=4444, debug=False)
