from flask import Flask
app = Flask(__name__)

@app.get("/")
def index():
    return "Hello v2 from Flask on Kubernetes (port 3000)!"

if __name__ == "__main__":
    # 在容器內聽 0.0.0.0:3000
    app.run(host="0.0.0.0", port=3000)
