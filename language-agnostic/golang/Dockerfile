FROM kestra/kestra:latest

USER root
RUN apt-get update && apt-get install -y golang-go && rm -rf /var/lib/apt/lists/*

CMD ["server", "standalone"]