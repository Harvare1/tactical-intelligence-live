FROM python:3.12-slim
WORKDIR /app
COPY engine.py server.py ./
COPY agents ./agents
COPY core ./core
COPY static ./static
USER 65532:65532
EXPOSE 8080
CMD ["python", "server.py"]
