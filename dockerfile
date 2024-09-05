FROM python:3.9-slim
ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY discordbot.py ./
COPY discord-app-434407-fed76dfbd5d6.json ./
CMD ["python", "discordbot.py"]