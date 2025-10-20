# ---- Builder Stage ----
# Installs dependencies using the locked requirements.txt.
FROM python:3.11-slim as builder

WORKDIR /app

# We need pip-tools to use pip-sync for a clean install
RUN pip install pip-tools

# Copy only the requirement files to leverage Docker's layer caching
COPY requirements.in requirements.txt ./

# Install dependencies from the locked file.
# Using 'pip-sync' is better than 'pip install -r' because it ensures
# that ONLY the packages in the file exist, creating a clean environment.
RUN pip-sync requirements.txt

# ---- Final Stage ----
# Copies only the necessary files and installed dependencies.
FROM python:3.11-slim

# Create a non-root user for better security
RUN useradd --create-home appuser
USER appuser
WORKDIR /home/appuser/app

# Copy installed Python packages from the builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# Copy the application source code
COPY ./src/app/ ./app/

# Healthcheck to verify the API is running before marking the container as healthy
HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Expose the port the app runs on
EXPOSE 8000

# Command to run the Uvicorn server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]