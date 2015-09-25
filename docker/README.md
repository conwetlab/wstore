# How to use this Dockerfile

You can build a docker image based on this Dockerfile. This image will contain only a WStore instance, exposing port `8000`. This requires that you have [docker](https://docs.docker.com/installation/) installed on your machine.

If you just want to have a WStore running as quickly as possible jump to section *The Fastest Way*.

If you want to know what is behind the scenes of our container you can go ahead and read the build and run sections.

## The Fastest Way

To run WStore using Docker, just run the following command (*replace `PORT` by the port of your local machine that will be used to access the service*):

```
sudo docker run -d --name wstore -p PORT:8000 conwetlab/wstore 
```

You can access the WStore with a default user with user name `admin` and password `admin`. 

## Build the image

If you have downloaded the [WStore's source code](https://github.com/conwetlab/wstore/) you can build your own image. The end result will be the same, but this way you have a bit more of control of what's happening.

To create the image, just navigate to the `docker` directory and run:

    sudo docker build -t wstore .

> **Note**
> If you do not want to have to use `sudo` in this or in the next section follow [these instructions](http://askubuntu.com/questions/477551/how-can-i-use-docker-without-sudo).


The parameter `-t wstore` gives the image a name. This name could be anything, or even include an organization like `-t conwetlab/wstore`. This name is later used to run the container based on the image.

If you want to know more about images and the building process you can find it in [Docker's documentation](https://docs.docker.com/userguide/dockerimages/).
    
### Run the container

The following line will run the container exposing port `8000`, give it a name -in this case `wstore1`. This uses the image built in the previous section.

    sudo docker run -d --name wstore1 -p 8000:8000 wstore

As a result of this command, there is WStore listening on port 8000 on localhost.

A few points to consider:

* The name `wstore1` can be anything and doesn't have to be related to the name given to the docker image in the previous section.
* In `-p 8000:8000` the first value represents the port to listen on localhost. If you want to run a second WStore on your machine you should change this value to something else, for example `-p 8001:8000`.
