import json
import os
from pprint import pprint

ROOT = os.path.dirname(os.path.dirname(__file__))
ACCOUNTS_PATH = os.path.join(ROOT, 'app', 'data', 'accounts.json')


def load_accounts(path=ACCOUNTS_PATH):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    accounts = load_accounts()
    pprint(accounts)


if __name__ == '__main__':
    main()
