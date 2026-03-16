FROM node:20-alpine AS build

WORKDIR /app

COPY package.json ./

RUN npm install --legacy-peer-deps && \
    npm install ajv@^8 --legacy-peer-deps

COPY . .

ARG REACT_APP_BACKEND_URL=http://localhost:8001
ENV REACT_APP_BACKEND_URL=$REACT_APP_BACKEND_URL

RUN npx craco build

# Production stage - serve static files
FROM node:20-alpine

WORKDIR /app

RUN npm install -g serve

COPY --from=build /app/build ./build

EXPOSE 3000

CMD ["serve", "-s", "build", "-l", "3000"]
