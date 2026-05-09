FROM python:3.7-slim

WORKDIR /app


# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    rm requirements.txt

# Copy application code
COPY pointsbot ./pointsbot
COPY pointsbot.py .


# Set environment to use unbuffered Python output
ENV PYTHONUNBUFFERED=1

# Run the bot
CMD ["python", "pointsbot.py"]
