# oh-my-scrapper - v0.1.1

This project aims to create a text-based scraper containing links to create a
final PDF with general information about job openings.

## Scope

- Read texts;
- Extract links;
- Use meta og:tags to extract information;

## Installation
I recomend to use a virtual environment, but you can make it directely.
That's optional:
```shell
python3 -m venv venv
```

And install dependencies:
```shell
pip install -r requirements.txt
```

## How to use

First we load a text file you would like to look for urls, the idea here is to
use the whatsapp history, but it works with any txt file.

The default file is `input/_chat.txt`. If you have the default file you just use
the command `load-txt`:
```shell
python3 main.py load-txt
```
or, if you have another file, just use the argument `-file` like this:
```shell
python3 main.py load-txt -file=my-text-file.txt
```
That will create a database if it doesn't exist and store every url the oh-my-scrapper
find. After that, let's scrap the urls with the command `scrap-urls`:

```shell
python3 main.py scrap-urls
```

That will scrap only the linkedin urls we are interested in. For now they are:
- linkedin_post: https://%.linkedin.com/posts/%
- linkedin_redirect: https://lnkd.in/%
- linkedin_job: https://%.linkedin.com/jobs/view/%
- linkedin_feed" https://%.linkedin.com/feed/%
- linkedin_company: https://%.linkedin.com/company/%

But we can use every other one generically using the argument `--ignore-type`:
```shell
python3 main.py scrap-urls --ignore-type
```

And we can ask to make it recursively adding the argument `--recursive`:
```shell
python3 main.py scrap-urls --recursive
```
> !!! important: we are not sure about blocks we can have for excess of requests

That's the basic usage!
But you can understand more using the help:
```shell
python3 main.py --help
```
