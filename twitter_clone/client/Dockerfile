FROM nginx:latest

RUN apt-get update && apt-get install -y nginx

RUN rm -f /etc/nginx/nginx.conf /etc/nginx/conf.d/default.conf

COPY client/static/css /usr/share/nginx/html/static
COPY client/static/js /usr/share/nginx/html/static
COPY client/static/images /usr/share/nginx/html/static
COPY client/static/favicon.ico /usr/share/nginx/html
COPY client/index.html /usr/share/nginx/html
COPY client/nginx.conf /etc/nginx/nginx.conf

CMD ["nginx", "-g", "daemon off;"]