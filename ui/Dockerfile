# Demo UI image: build the Vite app, then serve the static output with nginx.
#
# Build context is ui/. See docs/DECISIONS.md ("Docker Compose Topology For
# The Local Full Stack") for image choices.

FROM node:24-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:stable-alpine AS runtime

COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
