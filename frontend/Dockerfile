FROM node:22-slim

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm install

COPY . .

ARG NUXT_PUBLIC_API_BASE=https://verse-api.alifpunya.com
ENV NUXT_PUBLIC_API_BASE=$NUXT_PUBLIC_API_BASE

RUN npm run build

EXPOSE 3000

CMD ["node", ".output/server/index.mjs"]
