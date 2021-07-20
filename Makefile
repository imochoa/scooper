# vim:ft=make:

# Auto variables
MAKEFILE_PATH := $(abspath $(lastword $(MAKEFILE_LIST)))
REPO_DIR:=$(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))
DATE:=$(shell date)
CURRENT_UID := $(shell id -u)
CURRENT_GID := $(shell id -g)

TMP_DIR := ${REPO_DIR}/tmp

IMG_UBUNTU=scooper-ubuntu
IMG_ALPINE=scooper

.PHONY: help
help:
	cat Makefile

.PHONY: build-ubuntu
build-ubuntu:
	docker build                     \
		-f provision/Dockerfile-ubuntu \
		-t ${IMG_UBUNTU}               \
		.

.PHONY: run-ubuntu
run-ubuntu:
	docker run                                                 \
		--rm                                                     \
		-it                                                      \
		--user username:${GID}                                   \
		-v `pwd`:/inputs/                                        \
		--mount type=bind,source=`pwd`,target=/outputs/,readonly \
		${IMG_UBUNTU}

		#v `pwd`:/outputs/ \

.PHONY: debug-ubuntu
debug-ubuntu:
	docker run --rm -it ${IMG_UBUNTU}
