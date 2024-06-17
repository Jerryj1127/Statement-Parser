from creditcard.axis import AxisCreditCard
from creditcard.hdfc import HDFCCreditCard
    
passwd = "ABCD0100"


x = AxisCreditCard("Axis Credit Card Statement.pdf", password = passwd)
x.to_csv()


y = HDFCCreditCard("HDFC Credit Card Statement.pdf", password = passwd)
y.to_csv()