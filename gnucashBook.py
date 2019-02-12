from decimal import Decimal
from gnucash import Session, Transaction, Split, GncNumeric
import datetime

class GnucashSplit(object):

    def __init__(self, account, amount, memo=''):
        self.account = account
        self.amount = amount
        self.memo = memo
        self.parent = None

    def setParent(self, transaction):
        transaction.add_split(self)
        self.parent = transaction

class GnucashTransaction(object):
    """docstring for GnucashTransaction."""
    def __init__(self, datetime, description, note):
        self.datetime = datetime
        self.description = description
        self.note = note
        self.splits = []

    def add_split(self, split):
        self.splits.append(split)

class GnucashBook(object):
    """docstring for GnucashBook."""
    def __init__(self, file, currency, is_new=False):
        self.session = Session(file, is_new)
        try:
            self.book = self.session.book
            self.commod_tab = self.book.get_table()
            self.currency = self.commod_tab.lookup('ISO4217', currency)
            self.root = self.book.get_root_account()
        except Exception as ex:
            pass
#            logging.error(ex)

    def lookup_account_by_path(self, root, path):
        acc = root.lookup_by_name(path[0])
        if acc.get_instance() == None:
            raise Exception('Account path {} not found'.format(':'.join(path)))
        if len(path) > 1:
            return GnucashBook.lookup_account_by_path(self, acc, path[1:])
        return acc

    def lookup_account(self, name):
        path = name.split(':')
        return GnucashBook.lookup_account_by_path(self, self.root, path)

    def write_transactions(self, transactions):
        for transaction in transactions:

            tx = Transaction(self.book)
            tx.BeginEdit()
            tx.SetCurrency(self.currency)
            tx.SetDateEnteredTS(datetime.datetime.now())
            tx.SetDatePostedTS(transaction.datetime)
            tx.SetDescription(transaction.description)
            tx.SetNotes(transaction.note)

            for split in transaction.splits:
                sp = Split(self.book)
                sp.SetParent(tx)
                sp.SetAccount(GnucashBook.lookup_account(self, split.account))
                sp.SetMemo(split.memo)
                amount = int(Decimal(split.amount) * self.currency.get_fraction())
                sp.SetValue(GncNumeric(amount, self.currency.get_fraction()))
                sp.SetAmount(GncNumeric(amount, self.currency.get_fraction()))

            tx.CommitEdit()

    def close(self, nochange):
        if not nochange:
            self.session.save()
        self.session.end()
