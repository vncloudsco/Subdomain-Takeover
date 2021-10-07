# Subdomain Takeover Checker
Check if a list of sites is vulnerable to a S3 Bucket or Cloudfront CNAME Hijack

## Installation
* Configure subdom_config.py with email and cloudfront settings

## Usage
$ python subdom-check.py -f list -m 

## Requirements
* python 2.7.13
* grequests
* boto3

