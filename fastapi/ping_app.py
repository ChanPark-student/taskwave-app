from fastapi import FastAPI
app = FastAPI()

@app.get("/ping/{n}")
def ping(n: int):
    return {"pong": n}
