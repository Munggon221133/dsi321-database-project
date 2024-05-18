# Use an official Miniconda image as a parent image
FROM continuumio/miniconda3

# Set the working directory
WORKDIR /app

# Install any needed packages specified in requirements.txt
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your app's source code from your host to your image filesystem.
COPY . /app

# Ensure all directories are writable
RUN chmod -R 755 /app
RUN mkdir -p /mlflow && chmod -R 755 /mlflow

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variables
ENV MLFLOW_BACKEND_URI=postgresql+psycopg2://postgres:1234@172.25.16.1:5432/dsi324_mlflow
ENV MLFLOW_ARTIFACT_ROOT=/mlflow

# Run mlflow server when the container launches
CMD ["mlflow", "server", "--backend-store-uri", "${MLFLOW_BACKEND_URI}", "--default-artifact-root", "${MLFLOW_ARTIFACT_ROOT}", "--host", "0.0.0.0", "--port", "5000"]