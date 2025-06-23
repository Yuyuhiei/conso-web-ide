# --- STAGE 1: Build the React App ---
# Use an official Node.js image to create the build artifacts.
FROM node:18-alpine AS build

# Set the working directory inside the container
WORKDIR /app

# Copy package.json and package-lock.json to leverage Docker cache
COPY package.json ./
COPY package-lock.json ./

# Install dependencies
RUN npm install

# Copy the rest of the frontend application code
COPY . .

# Build the static files for production
RUN npm run build


# --- STAGE 2: Serve the App with Nginx ---
# Use a lightweight Nginx image to serve the static files.
FROM nginx:stable-alpine

# Copy the built static files from the 'build' stage
COPY --from=build /app/build /usr/share/nginx/html

# When the container starts, Nginx will automatically serve the files.
# Expose port 80
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]