import argparse


def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("-db", "--database", type=str,
                        help="Connect to preferred db", default="menfess_twitter")
    parser.add_argument("-mf", "--menfess", type=str,
                        help="Choose menfess to connect", required=True)

    return parser.parse_args()
