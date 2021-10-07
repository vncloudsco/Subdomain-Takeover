import os
import sys
import argparse
import smtplib
import re
import add_to_cf
import add_to_s3
import grequests
import subdom_config


def send_alert_mail(email_subject, email_body):
    """
    Sends alert email to the address specified in the config file.
    Borrowed from http://jmduke.com/posts/how-to-send-emails-through-python-and-gmail/
    """

    if EMAIL_ON:
        GMAIL_USERNAME = subdom_config.GMAIL_USERNAME
        GMAIL_PASSWORD = subdom_config.GMAIL_PASSWORD
        ALERT_ADDRESS = subdom_config.ALERT_ADDRESS

        session = smtplib.SMTP('smtp.gmail.com', 587)
        session.ehlo()
        session.starttls()
        session.login(GMAIL_USERNAME, GMAIL_PASSWORD)

        headers = "\r\n".join(["from: " + GMAIL_USERNAME,
                               "subject: " + email_subject,
                               "to: " + ALERT_ADDRESS,
                               "mime-version: 1.0",
                               "content-type: text/plain"])

        content = headers + "\r\n\r\n" + email_body
        try:
            session.sendmail(GMAIL_USERNAME, ALERT_ADDRESS, content)
        except:
            print("[*] unable to send notification email for %s" % email_body)


def parse_file(fhandle):
    """
    Reads the input file and gets the list of sites
    """
    try:
        with open(fhandle, 'r') as f:
            sites = f.read().splitlines()
    except:
        raise
    else:
        return sites


def get_bucket_name(site_text):
    searchgroup = re.search(r'<bucketname>(.*)</bucketname>', site_text)
    bucket = searchgroup.group(1)
    return bucket


def get_cname(url):
    url = url.replace("http://", "")
    url = url.replace("https://", "")
    cname = url.replace("/", "")
    return cname

def check_if_s3_or_cf(list_of_requests):
    aws_list = []
    headers = grequests.imap(list_of_requests, size=25)
    for i in headers:
        if 'cloudfront' in str(i.headers) or 'AmazonS3' in str(i.headers):
            if i.url not in aws_list:
                aws_list.append(i.url)

    return aws_list

def check_sites(list_of_requests):
    results = grequests.imap(list_of_requests, size=25)

    for i in results:
        text = str(i.content).lower()

        if 'error from cloudfront' in text:
            print "cloudfront found", i.url
            cname = get_cname(i.url)

            if add_to_cf.add_to_cf(cname):
                print "cloudfront takeover:", i.url
                send_alert_mail("Cloudfront CNAME claimed", i.url)

        if 'nosuchbucket' in text:
            print "no such bucekt found", i.url
            bucket = get_bucket_name(text)

            if add_to_s3.add_to_s3(bucket):
                print "no such bucket:", i.url
                send_alert_mail("S3 bucket claimed", i.url)


def command_line():
    parser = argparse.ArgumentParser(description="Check sites for missing S3 bucket or Cloudfront CNAMEs")
    parser.add_argument("-f", "--file", metavar="list_to_check", help="Supply a list file of sites.\nEx: sites.txt")
    parser.add_argument("-m", "--mail", help="enable mailed results", action="store_true")

    # command line args
    args = parser.parse_args()

    # Email flag
    global EMAIL_ON
    EMAIL_ON = False

    if args.mail:
        EMAIL_ON = True
        print ("[*] Results will be mailed to %s" % subdom_config.ALERT_ADDRESS)
    else:
        print ("[*] Config File Not Specified.  No Email Alerts will be sent")

    # If we have a list, do work
    if args.file:
        print ("[*] Parsing file \"%s\"" % args.file)
        if os.path.exists(args.file):
            sites = parse_file(args.file)
            site_list_with_protocol = []
            rs = []

            for y in xrange(len(sites)):
                site_list_with_protocol.append("http://" + str(sites[y]))
                site_list_with_protocol.append("https://" + str(sites[y]))
            rs = (grequests.head(s, timeout=2) for s in site_list_with_protocol)
            only_aws_sites = check_if_s3_or_cf(rs)
            
            reqs = (grequests.get(site, timeout=1) for site in only_aws_sites) 
            check_sites(reqs)

    else:
        print "[*] You must specify a file (-f)\n"
        sys.exit()


if __name__ == "__main__":
    command_line()
