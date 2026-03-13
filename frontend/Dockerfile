FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package.json ./

# Install ajv v8 explicitly to fix ajv-keywords peer dependency issue
# then install all deps
RUN npm install --legacy-peer-deps && \
    npm install ajv@^8 --legacy-peer-deps

# Copy source
COPY . .

EXPOSE 3000

ENV REACT_APP_BACKEND_URL=http://localhost:8001

CMD ["npx", "craco", "start"]
