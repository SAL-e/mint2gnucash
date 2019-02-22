from decimal import *
from hashlib import sha256

class MintTag(object):
    """docstring for MintTag."""

    def __init__(self, label):
        self.label = label

    def __str__(self):
        return '#'+self.label+' '

class MintTransaction(object):

    def __init__(self, date, description, originalDescription, amount, transactionType, category, accountName, labels, notes):
        self.date = date
        self.description = description
        self.originalDescription = originalDescription
        self.amount = amount
        self.transactionType = transactionType
        self.category = category
        self.accountName = accountName
        self.lables_raw = labels
        self.labels = []
        for label in labels.split():
            self.labels.append(MintTag(label))
        self.notes = notes
        self.setID()

    def __init__(self, csvRow):
        self.date = csvRow[0]
        self.description = csvRow[1]
        self.originalDescription = csvRow[2]
        self.amount = csvRow[3]
        self.transactionType = csvRow[4]
        self.category = csvRow[5]
        self.accountName = csvRow[6]
        self.lables_raw = csvRow[7]
        self.labels = []
        for label in csvRow[7].split():
            self.labels.append(MintTag(label))
        self.notes = csvRow[8]
        self.setID()

    def __str__(self):
        return '|' + self.date \
            + '|' + self.description \
            + '|' + self.originalDescription \
            + '|' + self.amount \
            + '|' + self.transactionType \
            + '|' + self.category \
            + '|' + self.accountName \
            + '|' + self.lables_raw \
            + '|' + self.notes \
            + '|'

    def getSplitAmount(self):
        amount = Decimal(self.amount)
        if self.transactionType == 'credit':
            amount = amount * Decimal('-1')
        return amount

    def getLabelsStr(self):
        lables = ''
        for l in self.labels:
            lables = lables + l.__str__()
        return lables

    def setID(self):
        self.id = sha256(self.__str__()).hexdigest()

    def getMintFileds(self):
        return [self.date, \
            self.description, \
            self.originalDescription, \
            self.amount, \
            self.transactionType, \
            self.category, \
            self.accountName, \
            self.lables_raw, \
            self.notes]

class MintSplit(object):

    def __init__(self, transaction, transactions):
        self.transactions = []
        self.transactions.append(transaction)
        i = 0
        while i < len(transactions):
            if transaction.date == transactions[i].date and \
            transaction.description == transactions[i].description and \
            transaction.transactionType == transactions[i].transactionType and \
            transaction.accountName != "Cash" and \
            transaction.accountName == transactions[i].accountName and \
            transaction.category != transactions[i].category:
                self.transactions.append(transactions.pop(i))
            else:
                i += 1

    def printSplit(self):
        print('split -------------------------------------')
        for transaction in self.transactions:
            print(transaction)

    def getAccountName(self):
        return self.transactions[0].accountName

    def getDate(self):
        return self.transactions[0].date

    def getDescription(self):
        return self.transactions[0].description

    def getOriginalDescription(self):
        return self.transactions[0].originalDescription

    def getTotal(self):
        total = Decimal('0.00')
        for transaction in self.transactions:
            total = total + Decimal(transaction.amount)
        if self.transactions[0].transactionType == 'debit':
            total = total * Decimal('-1')
        return total

    def getTransactions(self):
        return self.transactions

    def __str__(self):
        return '|' + self.getDate() \
            + '|' + self.getAccountName() \
            + '|' + self.getDescription() \
            + '|' + self.getOriginalDescription() \
            + '|' + str(self.getTotal()) \
            + '|'
