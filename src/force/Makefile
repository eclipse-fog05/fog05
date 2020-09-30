
REGISTRY?=fog05/force
TAG?=$(shell git describe --tags --dirty)
ARCH?=amd64

all:
	go build -o force src/app.go src/force.go src/main.go

clean:
	rm -rf force


# image:
# 	docker build -f Dockerfile.$(ARCH) -t $(REGISTRY):$(TAG)-$(ARCH) .
