# Warning, this will clean your entire database of data
docker compose down
docker rm -f $(docker ps -a -q)
docker volume rm $(docker volume ls -q)
docker image rm $(docker image ls | grep nodewatcher | awk {'print $3'})
docker compose up