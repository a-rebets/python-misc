import argparse
import smtplib
import ssl
import sys
import re
import random
import logging
import requests
import bs4
from datetime import datetime
from email.message import EmailMessage
from email.utils import formataddr

ENCODING = 'utf-8'
CONFIG_FILE_PATH = 'env.config'
CONFIG = {}

config_header_pattern = re.compile('\[(\w+)\]\s*')
config_body_pattern = re.compile('(\w+)\=(.*)')
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s > %(message)s',
                    datefmt='%d/%m/%Y %I:%M:%S %p', filename='output.log')


def run():
    parser = argparse.ArgumentParser(
        description='A mail processing / web scrapping app')
    parser.add_argument(
        '-m', '--mail', help='a message to be sent via e-mail', nargs='*')
    parser.add_argument('-pn', '--poke-names',
                        help='print the specified number of pokemon names')
    parser.add_argument(
        '-r', '--researchers', help='print the list of researchers starting with the specified letter')
    args = parser.parse_args()
    process_config(load_file_lines(CONFIG_FILE_PATH, ENCODING))
    timestamp = f'{datetime.now().strftime("%d-%m-%Y-%H_%M_%S")}'
    # send email
    if args.mail:
        send_mail(f'{timestamp}\t{args.mail[0]}')
    elif args.mail is not None:
        send_mail(timestamp)
    if args.researchers:
        print_researchers(args.researchers)
    if args.poke_names:
        print_pokemon_names(int(args.poke_names))


def send_mail(message):
    msg = EmailMessage()
    msg.set_content(message)
    msg['From'] = formataddr(('Artem Popelyshev', CONFIG['user']))
    msg['To'] = CONFIG['recipient_mail']
    msg['Subject'] = 'Test Message Header'
    context = ssl.create_default_context()
    try:
        with smtplib.SMTP(CONFIG['smtp_server'], int(CONFIG['port'])) as server:
            server.starttls(context=context)
            server.login(CONFIG['user'], CONFIG['password'])
            dict = server.sendmail(
                CONFIG['user'], CONFIG['recipient_mail'], msg.as_string())
            if not dict:
                print('Message sent successfully!')
    except smtplib.SMTPException as e:
        print('A problem occured while sending your message - check logs!')
        logging.error(str(e))

# Changed to requesting Pokemon names cause the Cats API was broken


def print_pokemon_names(num):
    print('Random pokemon names:')
    response = requests.get(
        f'https://pokeapi.co/api/v2/pokemon/?offset={random.randint(0, 1100-num)}&limit={num}')
    facts = response.json()['results']
    for k in range(num):
        print(f'#{k+1} - {facts[k]["name"]}')


def print_researchers(letter):
    page = requests.get('https://wiz.pwr.edu.pl/pracownicy?letter=' + letter)
    page.raise_for_status()

    content = bs4.BeautifulSoup(page.text, 'html.parser')
    names = content.find_all('a', attrs={'class': 'title'})
    mails = content.find_all('p')
    if names:  # In case no surnames starting with letter
        print(f'Researchers for the letter - {letter}')
        for mail, name in zip(mails, names):
            print(f'{name.getText()} - {mail.getText()}')
    else:
        msg = f'No surnames starting with: {letter}'
        print(msg)
        logging.warning(msg)


def process_config(lines):
    global CONFIG
    cur_title = ''
    for line in lines:
        header_match = config_header_pattern.match(line)
        body_match = config_body_pattern.match(line)
        if header_match != None:
            cur_title = header_match.group(1)
        elif body_match != None:
            par_name = body_match.group(1)
            par_val = body_match.group(2)
            if cur_title == 'Config':
                CONFIG[par_name] = par_val


def load_file_lines(path, encoding):
    result = []
    try:
        with open(path, encoding=encoding) as stream:
            for line in stream:
                if line == '':
                    break
                result.append(line.strip())
        return result
    except OSError:
        sys.stderr.write('File with the specified'
                         + ' name cannot be opened / found !')
        exit(1)


if __name__ == '__main__':
    run()
