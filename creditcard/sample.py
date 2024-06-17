import re
from datetime import datetime
from creditcard.cc import CreditCard, Transaction
from creditcard.config import Config

class AxisCreditCard(CreditCard):

    def __init__(self, statement_location, password) -> None:
        self.bank_name = ""
        super().__init__(statement_location, password)

    

    def set_metadata(self):
        initial_index = self.raw_text.find("INSERT KEYWORD")
        self.metadata = self.raw_text[:initial_index]

    def get_transaction_indices(self) -> list:
        pages = self.pages
        start_index = (1,3) # -> edit
        # skip the last page and moving in reverse
        for page_no, page in enumerate(pages[-2::-1]): 
            tables = page.extract_table()
            for row_no, row in enumerate(tables[::-1]): # moving in rev
                line = " ".join(filter(None, row))
                if '**** End of Statement ****' in line: # -> edit
                    last_index = (len(pages)-page_no-1, len(row)-row_no-1)
                    break

        return start_index, last_index
    
    def set_transactions(self, 
                            starting_page = 1, # 1st page
                            starting_row = 1,  # from third row
                            ending_page = -1,  # till n-1 th page
                            ending_row = -1    # till n-1th row
                                    )-> list:
        super()._set_transactions(starting_page, starting_row, ending_page, ending_row)



    def clean_transaction(self, temp_trasnaction:list):
        date: datetime
        name = ""
        categeory = ""
        amount = 0.0
        type = "Debit" or "Credit"
        cashback = 0.0

        return [date, name, categeory, amount, type, cashback]

