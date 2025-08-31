from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, AgentType
from langchain.tools import Tool
import requests
import subprocess
import os
from datetime import datetime

# ======================
# GitHub 工具：讀取最新 commit
# ======================
def get_latest_commit(_input=""):
    token = os.getenv("GITHUB_TOKEN")
    repo = "ryanchen0218/myapp"   # ⚠️ 改成你的 GitHub repo
    url = f"https://api.github.com/repos/{repo}/commits"
    headers = {"Authorization": f"token {token}"} if token else {}
    resp = requests.get(url, headers=headers).json()
    if isinstance(resp, list) and len(resp) > 0:
        return resp[0]["sha"]
    return "No commits found"

# ======================
# Kubernetes 工具：列出 Pods
# ======================
def list_pods(_input=""):
    result = subprocess.run(
        ["kubectl", "get", "pods", "-o", "wide"],
        capture_output=True,
        text=True
    )
    return result.stdout if result.stdout else result.stderr

# ======================
# CI/CD 工具：Build + Push + Deploy
# ======================
def build_and_deploy(_input=""):
    docker_user = os.getenv("DOCKER_USERNAME")
    docker_pass = os.getenv("DOCKER_PASSWORD")
    repo = f"{docker_user}/myapp"   # ⚠️ 改成你的 Docker Hub repo

    # 登入 Docker
    login = subprocess.run(
        ["docker", "login", "-u", docker_user, "--password-stdin"],
        input=docker_pass,
        text=True,
        capture_output=True
    )
    if login.returncode != 0:
        return f"Docker login failed: {login.stderr}"

    # 建立唯一 tag
    tag = datetime.now().strftime("%Y%m%d%H%M")
    image = f"{repo}:{tag}"

    # Docker build
    build = subprocess.run(["docker", "build", "-t", image, "."], capture_output=True, text=True)
    if build.returncode != 0:
        return f"Docker build failed: {build.stderr}"

    # Docker push
    push = subprocess.run(["docker", "push", image], capture_output=True, text=True)
    if push.returncode != 0:
        return f"Docker push failed: {push.stderr}"

    # 更新 deployment.yaml
    try:
        with open("deployment.yaml", "r") as f:
            yaml_data = f.read()

        new_yaml = []
        for line in yaml_data.splitlines():
            if "image:" in line:
                new_yaml.append(f"        image: {image}")
            else:
                new_yaml.append(line)

        with open("deployment.yaml", "w") as f:
            f.write("\n".join(new_yaml))
    except Exception as e:
        return f"Failed to update deployment.yaml: {str(e)}"

    # Apply Deployment
    apply = subprocess.run(["kubectl", "apply", "-f", "deployment.yaml"], capture_output=True, text=True)
    if apply.returncode != 0:
        return f"Kubernetes apply failed: {apply.stderr}"

    return f"✅ Build & Deploy success! Image: {image}"

# ======================
# 工具集合
# ======================
tools = [
    Tool(name="GitHubLatestCommit", func=get_latest_commit, description="Get latest commit SHA from GitHub"),
    Tool(name="KubernetesListPods", func=list_pods, description="List pods in the Kubernetes cluster"),
    Tool(name="BuildAndDeploy", func=build_and_deploy, description="Build Docker image, push to DockerHub, update and apply Kubernetes deployment")
]

# ======================
# 初始化 LLM + Agent
# ======================
llm = ChatOpenAI(model="gpt-4", temperature=0)

agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

# ======================
# 測試執行
# ======================
print("🔍 GitHub 測試：")
print(agent.run("Find the latest commit SHA on the default branch"))

print("\n📦 Kubernetes 測試：")
print(agent.run("List all pods in the cluster"))

print("\n🚀 Build & Deploy 測試：")
print(agent.run("Build a new Docker image and deploy it to the Kubernetes cluster"))

