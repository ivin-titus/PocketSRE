FROM node:22-alpine AS web-build
WORKDIR /web
COPY src/web/package.json ./
RUN npm install
COPY src/web ./
RUN npm run build

FROM python:3.14-slim
WORKDIR /app
COPY pyproject.toml ./
RUN pip install --no-cache-dir .
COPY src ./src
COPY --from=web-build /web/dist ./src/web/dist
EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
