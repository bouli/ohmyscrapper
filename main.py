import argparse
from modules.classify_urls import classify_urls
from modules.check_url import check_url
from modules.load_txt import load_txt
from modules.seed import seed
from modules.scrap_urls import scrap_urls
from modules.show import show_urls, show_urls_valid_prefix

def main():
    parser = argparse.ArgumentParser(prog="ohmyscraper")
    parser.add_argument('--version', action='version', version='%(prog)s v0.1.0')

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    seed_parser = subparsers.add_parser("seed", help="Seed database. Necessary to classify urls.")

    classify_urls_parser = subparsers.add_parser("classify-urls", help="Classify loaded urls")
    classify_urls_parser.add_argument('--recursive', default=False, help='Run in recursive mode', action='store_true')

    load_txt_parser = subparsers.add_parser("load-txt", help="Load txt file")
    load_txt_parser.add_argument('--file', default="input/_chat.txt", help='File path. Default is input/_chat.txt')

    scrap_urls_parser = subparsers.add_parser("scrap-urls", help="Scrap urls")

    check_url_parser = subparsers.add_parser("check-url", help="Check url")
    check_url_parser.add_argument('--url', default="https://cesarcardoso.cc/", help='Url to check')

    show_urls_parser = subparsers.add_parser("show", help="Show urls and prefixes")
    show_urls_parser.add_argument("--prefixes", default=False, help="Show urls valid prefix", action='store_true')
    show_urls_parser.add_argument("--limit", default=0, help="Limit of lines to show")


    #TODO: What is that?
    #seed_parser.set_defaults(func=seed)
    #classify_urls_parser.set_defaults(func=classify_urls)
    #load_txt_parser.set_defaults(func=load_txt)

    args = parser.parse_args()

    if args.command == 'classify-urls':
        classify_urls(args.recursive)
        return

    if args.command == 'load-txt':
        load_txt(args.file_name)
        return

    if args.command == 'seed':
        seed()
        return

    if args.command == 'check-url':
        check_url(args.url)
        return

    if args.command == 'scrap-urls':
        scrap_urls()
        return

    if args.command == 'show':
        if args.prefixes:
            show_urls_valid_prefix(int(args.limit))
            return

        show_urls(int(args.limit))
        return


if __name__ == "__main__":
    main()
