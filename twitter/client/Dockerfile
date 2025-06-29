FROM nginx

RUN apt-get update && apt-get install -y nginx

RUN rm /etc/nginx/nginx.conf /etc/nginx/conf.d/default.conf

COPY /client /client
COPY /client/nginx.conf /etc/nginx/nginx.conf

WORKDIR /client

CMD ["nginx", "-g", "daemon off;"]