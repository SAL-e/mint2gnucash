#!/usr/bin/env python

VERSION = "0.1"

# python imports
import argparse
import logging
import os
#import json
import csv
import datetime

#from mint import MintTransaction, MintSplit
from mint import *
from gnucashBook import GnucashBook, GnucashTransaction, GnucashSplit

def parse_cmdline():
    parser = argparse.ArgumentParser()
#    parser.add_argument('-i', '--imbalance-ac', default="Imbalance-[A-Z]{3}",
#                        help="Imbalance account name pattern. Default=Imbalance-[A-Z]{3}")
    parser.add_argument('--version', action='store_true',
                        help="Display version and exit.")
#    parser.add_argument('-m', '--use_memo', action='store_true',
#                        help="Use memo field instead of description field to match rules.")
    parser.add_argument('-v', '--verbose', action='store_true',
                        help="Verbose (debug) logging.")
    parser.add_argument('-q', '--quiet', action='store_true',
                        help="Suppress normal output (except errors).")
    parser.add_argument('-n', '--nochange', action='store_true',
                        help="Do not modify gnucash file. No effect if using SQL.")
    parser.add_argument('-e', '--expiration', dest='expirationDate',
                        help="Transaction expiration date in Mint.com format m/d/YYYY. Default Janurary 1st, Current Year. Expired transactions are ignored by mint2gnucash.")
#    parser.add_argument(
#        "ac2fix", help="Full path of account to fix, e.g. Liabilities:CreditCard")
    parser.add_argument("accountsfile", help="Accounts file. See doc for format.")
    parser.add_argument("categoriesfile", help="Categories file. See doc for format.")
    parser.add_argument('-t', '--transactions', dest="transactionsfile",
        default="transactions.csv", help="CSV file of Mint.com transactions.")
    parser.add_argument("gnucash_file", help="GnuCash file to modify.")
    args = parser.parse_args()
    return args

def readAccounts(filename):
    '''Read the accounts file.
    Populate an list with results. The list contents are:
    ([account], [account name]), ([account], [account name]) ...
    Note, this is in reverse order from the file.
    '''
    accounts = {}
    cvs_accounts = []
    with open(filename, 'r') as fd:
        accountsReader = csv.reader(fd)
        cvs_accounts = list(accountsReader)
    for line in cvs_accounts:
        if not line[0].startswith('#'):
            accounts[line[1]]=line[0]
    logging.debug(accounts)
    return accounts

def readCategories(filename):
    '''Read the categories file.
    Populate an list with results. The list contents are:
    ([category], [account name]), ([category], [account name]) ...
    Note, this is in reverse order from the file.
    '''
    categories = {}
    cvs_categories = []
    with open(filename, 'r') as fd:
        categoriesReader = csv.reader(fd)
        cvs_categories = list(categoriesReader)
#    cvs_categories = [line for line in cvs_categories if not line[0].startswith('#')]
    for line in cvs_categories:
        if not line[0].startswith('#'):
            categories[line[1]]=line[0]
    logging.debug(categories)
    return categories

def isExpired(transaction):
    return datetime.datetime.strptime(transaction.date,'%m/%d/%Y') < \
        expirationDT

def readTransactions(filename, log, fileMessage, isError=False):
    '''Read the Mint.com transactions file or transactions log.'''
    transactions = []
    logIDs = [l.id for l in log]
    logging.info(' Reading the '+fileMessage+' file: '+filename+' ...')
    exists = os.path.isfile(filename)
    if not exists:
        if isError:
            logging.error(' No '+fileMessage+' file found.')
        else:
            logging.warning(' No '+fileMessage+' file found.')
        return transactions
    with open(filename, 'r') as fd:
        transactionsReader = csv.reader(fd)
        for row in transactionsReader:
            if transactionsReader.line_num == 1:
                continue
            try:
                transaction = MintTransaction(row)
                if isExpired(transaction) or (transaction.id in logIDs):
                    logging.debug('[' + transaction.id + '] (skipped): ' + transaction.__str__())
                else:
                    logging.debug('reading: ' + transaction.__str__())
                    transactions.append( transaction )
            except IndexError:
                if row[0].startswith( '#' ):
                    logging.debug('comment (skipped):' + "|".join(row) )
                else:
                    logging.warning('malformed line (skipped):' + "|".join(row) )
    logging.info(' Done.')
    return transactions

def writeTransactionsLog(transactions, filename, begin, end):
    with open(filename, 'a') as fd:
        fd.write("# --- mint2gnucash.py: Session begins at: "+begin+" ---\n")
        transactionsWriter = csv.writer(fd, lineterminator='\n', quoting=csv.QUOTE_ALL)
        for transaction in transactions:
            logging.info(transaction)
            transactionsWriter.writerow(transaction.getMintFileds())
        fd.write("# --- mint2gnucash.py: Session ends at: "+end+" ---\n")

# Main entry point.
# 1. Parse command line.
# x. Read .gnucash-mint-import-cache.json
# 2. Open gnucash_file
# 3. Read all transactions.
# x. Save imported transactions into .gnucash-mint-import-cache.json
# 4. Close gnucash_file (without saving changes if --nochange is set)
#
def main():
    args = parse_cmdline()
    if args.version:
        print VERSION
        exit(0)

    if args.verbose:
        loglevel = logging.DEBUG
    elif args.quiet:
        loglevel = logging.WARN
    else:
        loglevel = logging.INFO
    logging.basicConfig(level=loglevel)

    global expirationDT
    if args.expirationDate:
        expirationDT=datetime.datetime.strptime(args.expirationDate,'%m/%d/%Y')
    else:
        expirationDT=datetime.datetime.strptime(str(datetime.datetime.now().year),'%Y')
    logging.info('Transaction expiration date: '+str(expirationDT))

    ##imported_cache = os.path.expanduser('~/.gnucash-mint-import-cache.json')
    #imported_cache = os.path.expanduser('.gnucash-mint-import-cache.json')
    #if os.path.exists(imported_cache):
    #    with open(imported_cache) as fd:
    #        imported = set(json.load(fd))
    #else:
    #    imported = set()

    gnucash_book = GnucashBook(args.gnucash_file, 'USD', is_new=False)

    accounts = readAccounts(args.accountsfile)
    categories = readCategories(args.categoriesfile)
    transactionsLog = readTransactions(args.transactionsfile+'.log', [], 'transactions log' )
    transactions = readTransactions(args.transactionsfile, transactionsLog, 'transactions', True)
    splits = []

    #if not args.nochange:
    #    with open(imported_cache, 'wb') as fd:
    #        json.dump(list(imported), fd)

    '''
    accounts = []
    for transaction in transactions:
        if not transaction.accountName in accounts:
            accounts.append(transaction.accountName)
    print('\n\n')
    print(accounts)
    '''

    while len(transactions) > 0:
        transaction = transactions.pop()
        splits.append(MintSplit(transaction,transactions))

    '''
    for split in splits:
        if len(split.transactions) > 1:
            split.printSplit()
    '''
    sessionBegins = str(datetime.datetime.now())
    transactionsImported = []
    for split in splits:
        transactionsCache = []
        print(split.getDate(),split.getAccountName(),split.getDescription(),split.getOriginalDescription(),split.getTotal())
        gnucash_transaction = GnucashTransaction(datetime.datetime.strptime(split.getDate(),'%m/%d/%Y'), split.getDescription(), split.getOriginalDescription())
        gnucash_split = GnucashSplit(accounts[split.getAccountName()],split.getTotal(),'mint2gnucash.py: '+str(datetime.datetime.now()))
        gnucash_split.setParent(gnucash_transaction)
        for transaction in split.getTransactions():
            gnucash_split = GnucashSplit(categories[transaction.category],transaction.getSplitAmount(),(transaction.notes+' ['+transaction.getLabelsStr()+']').strip())
            gnucash_split.setParent(gnucash_transaction)
            transactionsCache.append(transaction)
        gnucash_book.write_transactions([gnucash_transaction])
        for item in transactionsCache:
            transactionsImported.append(item)
    sessionEnds = str(datetime.datetime.now())

    gnucash_book.close(args.nochange)
    if not args.nochange:
        writeTransactionsLog(transactionsImported, args.transactionsfile+".log", sessionBegins, sessionEnds)

if __name__ == "__main__":
    main()
