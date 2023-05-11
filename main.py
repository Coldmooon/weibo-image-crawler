import argparse
from weibo import weibo_image_download as wb

parser = argparse.ArgumentParser(description='Weibo Image Crawler')
parser.add_argument('-l', '--link', default='', type=str, metavar='WeiboLink',
                    help='A Weibo link to download images. For example, https://weibo.com/3178232834/MFStocIKp or https://weibo.com/3178232834/4899808463031949')


def main():
    args = parser.parse_args()

    if args.link is not None:
        wb(args.link)
    else:
        print("Please provide a weibo link.")

if __name__ == '__main__':
    main()
