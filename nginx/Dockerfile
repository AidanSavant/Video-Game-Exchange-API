FROM nginx:latest

RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/nginx.conf

EXPOSE 80

# NOTE: Daemon off is required, otherwise docker container will exit immediately
CMD ["nginx", "-g", "daemon off;"]
