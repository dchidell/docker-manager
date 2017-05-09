# docker_manager
Manages docker containers.

```
usage: docker_deploy.py [-h] [-u] [-r] [-p] [-d] [-c] [-a]

optional arguments:
  -h, --help  show this help message and exit
  -u          Update container images
  -r          Redeploy existing containers / apps
  -p          Prune / delete stopped containers
  -d          Delete redundant images
  -c          Run for containers only (requires -r)
  -a          Run for apps only (requires -r)
```

Expects containers / docker-compose apps in the following structure:

```
root@docker:/home/david/host_scripts# tree
.
├── apps
│   └── webapps
│       ├── docker-compose.yml
│       └── docker-compose.yml.save
├── containers
│   ├── picserver2.txt
│   ├── picserver.txt
│   ├── plexpy.txt
│   ├── plex.txt
│   ├── portainer.old
│   ├── syncthing.txt
│   └── transmission.old
├── manager.py
```

Where each application docker-compose file is in it's own directory. Each container definition should be an executable bash file containing something like the following:

```
root@docker:/home/david/host_scripts# cat containers/transmission.old 
docker create \
--name=transmission \
-v /my/dir/tree/transmission_config:/config \
-v /my/dir/tree/Downloaded:/downloads \
-e PGID=0 -e PUID=0 \
--restart=always \
-p 9091:9091 -p 51413:51413 \
-p 51413:51413/udp \
linuxserver/transmission
root@docker:/home/david/host_scripts# 
```

The --name flag should match the name of the .txt file. 

If you want to disable a container from being involved with the process simply change the file extension to something other than .txt
