# OhMyScrapper - v0.1.1

This project aims to create a text-based scraper containing links to create a
final PDF with general information about job openings.

> This project is using [uv](https://docs.astral.sh/uv/getting-started/installation/#standalone-installer) by default.

## Scope

- Read texts;
- Extract links;
- Use meta og:tags to extract information;

## Installation

I recomend to use the [uv](https://docs.astral.sh/uv/getting-started/installation/#standalone-installer), so you can just use the command bellow and everything is installed:
```shell
uv sync
```

## How to use and test (development only)

OhMyScrapper works in 3 stages:

1. It collects and loads urls from a text (by default `input/_chat.txt`) in a database;
2. It scraps/access the collected urls and read what is relevant. If it finds new urls, they are collected as well;
3. Export a list of urls in CSV files;

You can do 3 stages with the command:
```shell
make start
```
> Remember to add your text file in the folder `/input` with the name `_chat.txt`!

You will find the exported files in the folder `/output` like this:
- `/output/report.csv`
- `/output/report.csv-preview.html`
- `/output/urls-simplified.csv`
- `/output/urls-simplified.csv-preview.html`
- `/output/urls.csv`
- `/output/urls.csv-preview.html`

### BUT: if you want to do step by step, here it is:

First we load a text file you would like to look for urls, the idea here is to
use the whatsapp history, but it works with any txt file.

The default file is `input/_chat.txt`. If you have the default file you just use
the command `load-txt`:
```shell
make load
```
or, if you have another file, just use the argument `-file` like this:
```shell
uv run main.py load-txt -file=my-text-file.txt
```
That will create a database if it doesn't exist and store every url the oh-my-scrapper
find. After that, let's scrap the urls with the command `scrap-urls`:

```shell
make scrap-urls
```

That will scrap only the linkedin urls we are interested in. For now they are:
- linkedin_post: https://%.linkedin.com/posts/%
- linkedin_redirect: https://lnkd.in/%
- linkedin_job: https://%.linkedin.com/jobs/view/%
- linkedin_feed" https://%.linkedin.com/feed/%
- linkedin_company: https://%.linkedin.com/company/%

But we can use every other one generically using the argument `--ignore-type`:
```shell
uv run main.py scrap-urls --ignore-type
```

And we can ask to make it recursively adding the argument `--recursive`:
```shell
uv run main.py scrap-urls --recursive
```
> !!! important: we are not sure about blocks we can have for excess of requests

And we can finally export with the command:
```shell
make export
```


That's the basic usage!
But you can understand more using the help:
```shell
uv run main.py --help
```
