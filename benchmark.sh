#!/bin/bash
stdbuf -o L `which time` -f "real\t%E\nuser\t%U\nsys\t%S\nmem\t%M/4 kB" $@ 2>&1
