# Austin Rose
# CS529 Spring 2015
# Project 1
# Makefile

CC=gcc

all: record play

record: record.c
	$(CC) -Wall -o record record.c -lm -lasound

play: play.c
	$(CC) -Wall -o play play.c -lm -lasound

clean:
	/bin/rm -rf record play 
