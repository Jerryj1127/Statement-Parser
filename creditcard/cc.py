from datetime import datetime
import pdfplumber, re, csv
from abc import ABC, abstractmethod
from creditcard.config import Config

class Transaction:
    VALID_TYPES = {"Credit", "Debit"}
    HEADERS = ["DATE", "NAME", "CATEGORY", "AMOUNT", "TYPE", "CASHBACK"]

    def __init__(self,
        date:datetime,
        name: str,
        category:str,
        amount: float,
        type:str,
        cashback: float = 0.0
                    ) -> None:
        
        if type not in self.VALID_TYPES:
            raise ValueError(f"Invalid transaction type: {type}. Must be 'Credit' or 'Debit'.")

        self.date = date
        self.name = name
        self.category = category
        self.amount = amount
        self.type = type
        self.cashback = cashback

    def to_list(self):
        return [
            self.date.strftime('%d/%m/%Y'),
            self.name,
            self.category,
            self.amount,
            self.type,
            self.cashback
        ]
    
    def to_dict(self):
        return {
            "DATE": self.date.strftime('%d/%m/%Y'),
            "NAME": self.name,
            "CATEGORY": self.category,
            "AMOUNT": self.amount,
            "TYPE": self.type,
            "CASHBACK": self.cashback
        }
    
    def __repr__(self):
        return (f"Transaction(date={self.date}, " \
                f"name='{self.name}', " \
                f"category='{self.category}', " \
                f"amount={self.amount}, " \
                f"type={self.type}, " \
                f"cashback={self.cashback}"
            )
    
    def __str__(self):
        return (f"{self.date.strftime('%d/%m/%Y')}, " \
                f"{self.name}, " \
                f"{self.category}, " \
                f"{self.amount}, " \
                f"{self.type}, " \
                f"{self.cashback}"
            )
    

# region CLASS: Creditcard

# skeleton
class CreditCard(ABC):
    #card data
    card_name:str  =""
    card_number = -9999
    owner_name = ""

    # limit data
    limit:int = 0
    current_usage = 0
    available_limit = 0
    outstanding = 0

    # dates
    statement_period = ""
    due_date = ""
    statement_generation_date = ""

    # transaction
    transactions:list[Transaction] = []


    def __init__(self, statement_location, password) -> None:
        self.type = "Credit Card"
        self.raw_data = pdfplumber.open(statement_location, password = password)
        self.pages = self.raw_data.pages
        self.raw_text = "\n".join([self.pages[i].extract_text() for i in range(len(self.pages))])
        self.__set()

    
    
    def __set(self):
        """method to calculate compute things from the statement"""
        self.set_metadata()
        self.get_card_name()
        self.get_card_4digits()
        self.set_transactions()

    # region methods on statement 

    # meta
    @abstractmethod
    def set_metadata(self):
        pass


    # pass : not all cards have the statement period info
    def get_statement_period(self):
        pass

    # todo, some cards have cashback points
    def get_total_cashback(self):
        pass

    def get_cashback_type(self):
        pass

    #todo
    def get_due_date(self):
        pass

    #todo
    def get_generation_date(self):
        pass

    # region methods on card 

    def get_card_name(self, index=0):
        self.card_name = self.metadata.split("\n")[index].replace("Statement","").strip()
        return self.card_name

    def get_card_4digits(self):
        self.card_number = re.search(Config.card_no_pattern, self.metadata).group(0)[-4:]
        return self.card_number
    

    # region methods on transaction 

    @abstractmethod
    def clean_transaction(self, transaction):
        pass

    @abstractmethod
    def set_transactions(self, starting_page, starting_row, ending_page, ending_row):
        pass

    def _set_transactions(self, 
                            starting_page = None,
                            starting_row = None,
                            ending_page = None,
                            ending_row = None) -> list:
        """Parent method for extracting transactions from a statement"""
        
        if starting_page<1:
            raise ValueError("Starting page should be greater than 0")
        elif ending_page==None:
            raise ValueError ("ending page cannot be None")

        # workaround for negative indices (as range needs 'step' calculation)
        len_pages = len(self.pages)
        x = list(range(0, len_pages))
        _ending_page = ending_page if ending_page>0 else len_pages+ending_page

        # starting_page-1 -> human format to array index correction
        for i in x[starting_page-1: ending_page]:
            current_table = self.pages[i].extract_table()
            start = starting_row if i==starting_page-1 else None
            stop = ending_row if i==_ending_page-1 else None

            for row in current_table[start:stop]:
                if __temp := self.clean_transaction(row):
                    self.transactions.append(Transaction(*__temp))
            
                
    def to_csv(self, filename=None, fields=[]):
        """Convert a Card statement's transactions to CSV file

        Parameters:
            filename (``str``  *optional*):
                Filename or path to the csv file thats to be created
                Leave it empty to use the default filename: ``card name - last 4 digits of card.csv``.
                Default path is the present working directory, specify a path with filename to change the directory


            
            fields (``list[str]`` *optional*):
                List of fields to include in the CSV file. 
                Available fields are: ``DATE``, ``NAME``, ``CATEGORY``, ``AMOUNT``, ``TYPE``, ``CASHBACK``.
                Default is to include all above fields. 
                Additonal fields to include (related to card) are :
                ``CARDNAME``, ``CARDNO``, ``CARDTYPE``, ``BANKNAME``. 
            """
        
        if not filename:
            filename = f"{self.card_name}-{self.card_number}.csv"
        if not filename.lower().endswith(".csv"):
            filename += ".csv"

        _row = []
        _header = []
        if 'CARDNAME' in fields:
            _row.append(self.card_name)
            _header.append('CARDNAME')
            fields.remove('CARDNAME')
        if 'CARDNO' in fields:
            _row.append(self.card_number)
            _header.append('CARDNO')
            fields.remove('CARDNO')
        if 'CARDTYPE' in fields:
            _row.append(self.type)
            _header.append('CARDTYPE')
            fields.remove('CARDTYPE')
        if 'BANKNAME' in fields:
            _row.append(self.bank_name)
            _header.append('BANKNAME')
            fields.remove('BANKNAME')
        
        if fields is None or fields==[]:
            fields = Transaction.HEADERS


        with open(filename, 'w') as csvfile:  

            csvwriter = csv.writer(csvfile)  

            csvwriter.writerow(fields+_header)  
                
            for transaction in self.transactions:
                transaction_dict = transaction.to_dict()
                row = [transaction_dict[field] for field in fields] + _row
                csvwriter.writerow(row)


        
        return filename

    def __str__(self):
        return f"{self.card_name} - {self.card_number}"
        
            
