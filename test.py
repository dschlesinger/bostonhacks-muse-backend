test_to_run: str = input('What test do you want to run?: ')

match test_to_run:

    case 'websocket':
        import uvicorn
        from server.websocket import app
        uvicorn.run(app, host="0.0.0.0", port=8000)