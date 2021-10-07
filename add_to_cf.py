import boto3
import json
import subdom_config


def add_to_cf(newsite):
    ID = subdom_config.CLOUDFRONT_ID
    client = boto3.client('cloudfront')
    response = client.get_distribution_config(Id=ID)

    # Get the ETAG so we can push changes
    ETAG = json.dumps(response['ETag'])
    ETAG = json.loads(ETAG)

    dist_conf = response['DistributionConfig']

    # Add our site to the list of Aliases Items
    dist_conf['Aliases']['Items'].append(newsite)
    cnames = dist_conf['Aliases']['Items']

    # update quantity of aliases
    newq = len(cnames)
    dist_conf['Aliases']['Quantity'] = newq

    # print dist_conf

    try:
        new = client.update_distribution(DistributionConfig=dist_conf, Id=ID, IfMatch=ETAG)
    except:
        return False
    else:
        return True


if __name__ == '__main__':
    newsite = 'test999.twitch.tv'
    add_to_cf(newsite)
