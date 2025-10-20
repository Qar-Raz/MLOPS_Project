# Project Setup

### 1. Clone the Repository
```bash
git clone https://github.com/Qar-Raz/MLOPS_Project.git
```

### 2. Create & Activate Virtual Environment
This isolates our project's dependencies from your system.

```bash
# Create the virtual environment
python -m venv .venv

# Activate the environment (choose the command for your OS)

# macOS / Linux
source .venv/bin/activate

# Windows (Git Bash)
source .venv/Scripts/activate```
> **Note:** You'll know it's working if you see `(.venv)` at the start of your terminal prompt.

### 3. Install All Dependencies

```bash
# Make sure your virtual environment is active!
pip install -r requirements.txt -r requirements-dev.txt
```

### 4. Activate Pre-Commit Hooks


```bash
pre-commit install
```
**You are now fully set up and ready to code!**

---

## Daily Development Workflow

1.  **Activate Environment:** Always start your work session by activating the virtual environment.
    ```bash
    source .venv/Scripts/activate
    ```2.  **Get Latest Changes & Create Branch:** Never work directly on `main`.
    ```bash
    git checkout main
    git pull origin main
    git checkout -b feat/your-descriptive-branch-name
    ```
3.  **Write Code!**
4.  **Commit Your Work:** Our pre-commit hooks will run automatically.
    ```bash
    git add .
    git commit -m "feat: your descriptive commit message"
    ```
    > **If your commit is stopped by the hooks:** It's usually because they automatically fixed a file. Just run `git add .` again and re-run your `git commit` command.

5.  **Push and Open a Pull Request:**
    ```bash
    git push origin feat/your-descriptive-branch-name
    ```
    Then, go to GitHub to open a Pull Request for review.
