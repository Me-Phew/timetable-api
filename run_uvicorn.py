import uvicorn

from init_app import init_app

if __name__ == "__main__":
    init_app()
    uvicorn.run("main:app", reload=True)
