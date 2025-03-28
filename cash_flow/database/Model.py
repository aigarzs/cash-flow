from sqlalchemy import Integer, String, DateTime, Numeric, ForeignKey, event, \
    text, Boolean, Float
from sqlalchemy.orm import DeclarativeBase, mapped_column, relationship

from cash_flow.database.Views import views_all


class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "A01_Users"

    id = mapped_column(String(100), primary_key=True)
    name = mapped_column(String(100), nullable=False)
    password = mapped_column(String(100), nullable=False)
    admin = mapped_column(Boolean, nullable=False, default=False)
    customers = mapped_column(Boolean, nullable=False, default=False)
    vendors = mapped_column(Boolean, nullable=False, default=False)
    reports = mapped_column(Boolean, nullable=False, default=False)

@event.listens_for(User.metadata, "after_create")
def default_data_sources(target, connection, **kw):
    table_name = User.__tablename__
    sql = ("INSERT INTO " + table_name +
           " (id, name, password, admin, customers, vendors, reports) " +
           " VALUES (:id, :name, :password, :admin, :customers, :vendors, :reports)")
    params = [{ "id": "root",
                "name": "Administrator",
                "password": "toor",
                "admin": True,
                "customers": True,
                "vendors": True,
                "reports": True
                },
            ]

    connection.execute(text(sql), params)

class Source(Base):
    __tablename__ = "A02_Sources"
    GENIE = 1
    DEFAULT = 2
    id = mapped_column(Integer, primary_key=True)
    type_id = mapped_column(ForeignKey("A03_SourceTypes.id", ondelete="CASCADE"))
    name = mapped_column(String(100), nullable=False)
    url = mapped_column(String(255), nullable=False)
    username = mapped_column(String(100))
    password = mapped_column(String(255))


@event.listens_for(Source.metadata, "after_create")
def default_data_sources(target, connection, **kw):
    table_name = Source.__tablename__
    sql = ("INSERT INTO " + table_name +
           " (id, type_id, name, url, username, password) " +
           " VALUES (:id, :type, :name, :url, :username, :password)")
    params = [{ "id": Source.GENIE,
                "type": SourceType.GENIE,
                "name": "Genie Cash Flow App",
                "url": "localhost",
                "username": "user",
                "password": "password"
                },
                {"id": Source.DEFAULT,
               "type": SourceType.TILDES_JUMIS,
               "name": "Tildes Jumis galvenā db",
               "url": "localhost:5210//jumis",
               "username": "user",
               "password": "password"},
              ]

    connection.execute(text(sql), params)

class SourceType(Base):
    __tablename__ = "A03_SourceTypes"
    GENIE = 1
    TILDES_JUMIS = 2
    id = mapped_column(Integer, primary_key=True)
    name = mapped_column(String(100))

@event.listens_for(SourceType.metadata, "after_create")
def default_data_source_types(target, connection, **kw):
    table_name = SourceType.__tablename__
    sql = "INSERT INTO " + table_name + " (id, name) VALUES (:id, :name)"
    params = [ {"id": SourceType.GENIE,
                "name": "Genie Cash Flow App"},
                {"id": SourceType.TILDES_JUMIS,
               "name": "Tildes Jumis"},
              ]

    connection.execute(text(sql), params)



class Currency(Base):
    __tablename__ = "B01_Currencies"
    code = mapped_column(String(10), nullable=False, primary_key=True)
    name = mapped_column(String(100), nullable=False)

class Account(Base):
    __tablename__ = "B02_Accounts"
    code = mapped_column(String(30), nullable=False, primary_key=True)
    name = mapped_column(String(100), nullable=False)
    type_id = mapped_column(ForeignKey("B03_AccountTypes.id"))

class AccountType(Base):
    __tablename__ = "B03_AccountTypes"

    BANK_ACCOUNT = 1
    CUSTOMERS_ACCOUNT = 2
    VENDORS_ACCOUNT = 3
    EXPENSES_ACCOUNT = 4
    REVENUES_ACCOUNT = 5
    TAX_ACCOUNT = 6

    id = mapped_column(Integer, primary_key=True)
    name = mapped_column(String(100), nullable=False)

@event.listens_for(AccountType.metadata, "after_create")
def default_data_account_types(target, connection, **kw):
    table_name = AccountType.__tablename__
    sql = "INSERT INTO " + table_name + " (id, name) VALUES (:id, :name)"
    params = [{"id": AccountType.BANK_ACCOUNT,
               "name": "Naudas līdzekļu konts"},
              {"id": AccountType.CUSTOMERS_ACCOUNT,
               "name": "Norēķini ar klientiem"},
              {"id": AccountType.VENDORS_ACCOUNT,
               "name": "Norēķini ar piegādātājiem"},
              {"id": AccountType.EXPENSES_ACCOUNT,
               "name": "Naudas izlietojuma konts"},
              {"id": AccountType.REVENUES_ACCOUNT,
               "name": "Naudas ieņēmumu konts"},
              {"id": AccountType.TAX_ACCOUNT,
               "name": "PVN konts"},
              ]

    connection.execute(text(sql), params)



class Customer(Base):
    __tablename__ = "B04_Customers"
    id = mapped_column(Integer, primary_key=True)
    name = mapped_column(String(100), nullable=False)
    source_id = mapped_column(ForeignKey("A02_Sources.id", ondelete="CASCADE"))
    source_key = mapped_column(String(30))
    priority = mapped_column(Integer, nullable=False)
    void = mapped_column(Boolean, nullable=False, default=False)

class Vendor(Base):
    __tablename__ = "B05_Vendors"
    id = mapped_column(Integer, primary_key=True)
    name = mapped_column(String(100), nullable=False)
    source_id = mapped_column(ForeignKey("A02_Sources.id", ondelete="CASCADE"))
    source_key = mapped_column(String(30))
    priority = mapped_column(Integer, nullable=False)
    void = mapped_column(Boolean, nullable=False, default=False)

class Document(Base):
    __tablename__ = "D01_Documents"

    id = mapped_column(Integer, primary_key=True)
    source_id = mapped_column(ForeignKey("A02_Sources.id", ondelete="CASCADE"), nullable=False)
    source_key = mapped_column(String(30), nullable=False)
    type_id = mapped_column(ForeignKey("D02_DocTypes.id"))
    date = mapped_column(DateTime, nullable=False, index=True)
    date_due = mapped_column(DateTime, nullable=False)
    date_planned_clearing = mapped_column(DateTime, nullable=False, index=True)
    date_cleared = mapped_column(DateTime, nullable=True)
    priority = mapped_column(Integer, nullable=False)
    number = mapped_column(String(30), nullable=False)
    customer_id = mapped_column(ForeignKey("B04_Customers.id"), nullable=True)
    vendor_id = mapped_column(ForeignKey("B05_Vendors.id"), nullable=True)
    description = mapped_column(String(255), nullable=False)
    amount = mapped_column(Numeric(12,2, 2), nullable=False)
    currency  = mapped_column(ForeignKey("B01_Currencies.code"), nullable=False)
    amount_LC = mapped_column(Numeric(12, 2, 2), nullable=False)
    memo = mapped_column(String)
    cleared = mapped_column(Boolean, nullable=False, default=0)
    cleared_amount = mapped_column(Numeric(12, 2), nullable=False, default=0)
    void = mapped_column(Boolean, nullable=False, default=0)
    gl = relationship("GeneralLedger", back_populates="document")

    def __repr__(self):
        type = "UNKNOWN"
        types = DocType.__dict__
        for t in types:
            if types[t] == self.type_id:
                type = t

        return f"<Document id={self.id} type={type}>"

class DocType(Base):
    __tablename__ = "D02_DocTypes"
    BANK_RECEIPT = 1
    BANK_PAYMENT = 2
    INVOICE_CUSTOMER = 3
    INVOICE_VENDOR = 4
    CREDITNOTE_CUSTOMER = 5
    CREDITNOTE_VENDOR = 6
    PAYROLL = 7
    id = mapped_column(Integer, primary_key=True)
    name = mapped_column(String(100))

@event.listens_for(DocType.metadata, "after_create")
def default_data_doc_types(target, connection, **kw):
    table_name = DocType.__tablename__
    sql = "INSERT INTO " + table_name + " (id, name) VALUES (:id, :name)"
    params = [{"id": DocType.BANK_RECEIPT,
               "name": "Ienākošais bankas maksājums"},
              {"id": DocType.BANK_PAYMENT,
               "name": "Izejošais bankas maksājums"},
              {"id": DocType.INVOICE_CUSTOMER,
                "name": "Rēķins klientam"},
              {"id": DocType.INVOICE_VENDOR,
               "name": "Rēķins no piegādātāja"},
              {"id": DocType.CREDITNOTE_CUSTOMER,
               "name": "Kredītrēķins klientam"},
              {"id": DocType.CREDITNOTE_VENDOR,
               "name": "Kredītrēķins no piegādātāja"},
              {"id": DocType.PAYROLL,
               "name": "Algu saraksts"},
              ]

    connection.execute(text(sql), params)

class GeneralLedger(Base):
    __tablename__ = "D03_GeneralLedger"
    id = mapped_column(Integer, primary_key=True)
    document_id = mapped_column(ForeignKey("D01_Documents.id", ondelete="CASCADE"), nullable=False)
    entry_type = mapped_column(String(2), nullable=False, index=True)
    account = mapped_column(ForeignKey("B02_Accounts.code"), nullable=False, index=True)
    amount = mapped_column(Numeric(12,2, 2), nullable=False)
    amount_LC = mapped_column(Numeric(12,2, 2), nullable=False)
    document = relationship("Document", back_populates="gl")

class Reconciliation(Base):
    __tablename__ = "D04_Reconciliations"
    id = mapped_column(Integer, primary_key=True)
    amount = mapped_column(Numeric(12,2), nullable=False)
    currency = mapped_column(ForeignKey("B01_Currencies.code"), nullable=False)
    date = mapped_column(DateTime, nullable=False)
    invoice_id = mapped_column(ForeignKey("D01_Documents.id"), nullable=False)
    payment_id = mapped_column(ForeignKey("D01_Documents.id"), nullable=False)
    source_id = mapped_column(ForeignKey("A02_Sources.id", ondelete="CASCADE"),
                              nullable=False)
    source_key = mapped_column(String(30), nullable=False)

class PlannedAnonymousOperation(Base):
    __tablename__ = "D05_PlannedAnonymousOperations"
    id = mapped_column(Integer, primary_key=True)
    name = mapped_column(String(100), nullable=True)

class PlannedAnonymousAccount(Base):
    __tablename__ = "D06_PlannedAnonymousAccounts"
    id = mapped_column(Integer, primary_key=True)
    operation_id = mapped_column(ForeignKey("D05_PlannedAnonymousOperations.id", ondelete="CASCADE"), nullable=False)
    entry_type = mapped_column(String(2), nullable=True, index=True)
    account = mapped_column(ForeignKey("B02_Accounts.code"), nullable=True, index=True)
    fraction = mapped_column(Float, nullable=True)

class PlannedAnonymousAmount(Base):
    __tablename__ = "D07_PlannedAnonymousAmounts"
    id = mapped_column(Integer, primary_key=True)
    operation_id = mapped_column(ForeignKey("D05_PlannedAnonymousOperations.id", ondelete="CASCADE"), nullable=False)
    date = mapped_column(DateTime, nullable=True, index=True)
    amount_LC = mapped_column(Numeric(12, 2, 2), nullable=True)

class CashFlowDefinition(Base):
    __tablename__ = "E01_CashFlowDefinition"
    TYPE_ACCOUNTS = 1
    TYPE_TOTALS = 2
    TYPE_BALANCE = 3
    id = mapped_column(Integer, primary_key=True)
    key = mapped_column(String(10), nullable=True)
    definition_type = mapped_column(Integer, nullable=True)
    name = mapped_column(String(100), nullable=True)

@event.listens_for(CashFlowDefinition.metadata, "after_create")
def default_data_doc_types(target, connection, **kw):
    table_name = CashFlowDefinition.__tablename__
    sql = "INSERT INTO " + table_name + " (key, definition_type, name) VALUES (:key, :type, :name)"
    params = [{"key": "100", "type": None, "name": "Pamatdarbības naudas plūsma"},
              {"key": "101", "type": 1, "name": "Ieņēmumi no preču un pakalpojumu pārdošanas"},
              {"key": "102", "type": 1, "name": "Maksājumi piegādātājiem"},
              {"key": "103", "type": 1, "name": "Maksājumi darbiniekiem"},
              {"key": "104", "type": 1, "name": "Pārējie pamatdarbības ieņēmumi un izdevumi"},
              {"key": "199", "type": 2, "name": "Bruto pamatdarbības naudas plūsma"},
              {"key": "201", "type": 1, "name": "Izdevumi procentu maksājumiem"},
              {"key": "202", "type": 1, "name": "Izdevumi nodokļu maksājumiem"},
              {"key": "203", "type": 1, "name": "Naudas plūsma no ārkārtas posteņiem"},
              {"key": "299", "type": 2, "name": "Pamatdarbības neto naudas plūsma"},
              {"key": "300", "type": None, "name": "Ieguldīšanas darbības naudas plūsma"},
              {"key": "301", "type": 1, "name": "Radniecīgo vai asociēto uzņēmumu daļu iegāde"},
              {"key": "302", "type": 1, "name": "Ieņēmumi no radniecīgo vai asociēto uzņēmumu daļu pārdošanas"},
              {"key": "303", "type": 1, "name": "Pamatlīdzekļu un nemateriālo ieguldījumu iegāde"},
              {"key": "304", "type": 1, "name": "Ieņēmumi no pamatlīdzekļu un nemateriālo ieguldījumu pārdošanas"},
              {"key": "305", "type": 1, "name": "Izsniegtie aizdevumi"},
              {"key": "306", "type": 1, "name": "Ieņēmumi no aizdevumu atmaksas"},
              {"key": "307", "type": 1, "name": "Saņemtie procenti"},
              {"key": "308", "type": 1, "name": "Saņemtās dividendes"},
              {"key": "309", "type": 2, "name": "Ieguldījumu darbības neto naudas plūsma"},
              {"key": "400", "type": None, "name": "Finansēšanas darbības naudas plūsma"},
              {"key": "401", "type": 1, "name": "Ieņēmumi no akciju vai obligāciju emisijas"},
              {"key": "402", "type": 1, "name": "Saņemtie aizņēmumi"},
              {"key": "403", "type": 1, "name": "Izdevumi aizdevumu atmaksai"},
              {"key": "404", "type": 1, "name": "Samaksātie procenti"},
              {"key": "405", "type": 1, "name": "Izmaksātās dividendes"},
              {"key": "499", "type": 2, "name": "Finansēšanas darbības neto naudas plūsma"},
              {"key": "901", "type": 1, "name": "Ārvalstu valūtu kursu svārstību rezultāts"},
              {"key": "902", "type": 2, "name": "Neto naudas plūsma"},
              {"key": "999", "type": 3, "name": "Naudas līdzekļu atlikums pārskata perioda beigās"}
              ]

    connection.execute(text(sql), params)

class CashFlowDefinitionAccount(Base):
    __tablename__ = "E01_CashFlowDefinitionAccounts"
    id = mapped_column(Integer, primary_key=True)
    definition_id = mapped_column(ForeignKey("E01_CashFlowDefinition.id"), nullable=True)
    operator = mapped_column(String(1), nullable=True)
    entry_type = mapped_column(String(2), nullable=True)
    account = mapped_column(ForeignKey("B02_Accounts.code"), nullable=True)

class CashFlowDefinitionTotal(Base):
    __tablename__ = "E01_CashFlowDefinitionTotals"
    id = mapped_column(Integer, primary_key=True)
    definition_id = mapped_column(ForeignKey("E01_CashFlowDefinition.id"), nullable=True)
    operator = mapped_column(String(1), nullable=True)
    definition_summarized = mapped_column(ForeignKey("E01_CashFlowDefinition.id"), nullable=True)

class BudgetEntry(Base):
    __tablename__ = "F01_BudgetEntries"
    id = mapped_column(Integer, primary_key=True)
    definition_id = mapped_column(ForeignKey("E01_CashFlowDefinition.id"), nullable=False)
    date = mapped_column(DateTime, nullable=True, index=True)
    amount_LC = mapped_column(Numeric(12, 2, 2), nullable=True)
    memo = mapped_column(String(250), nullable=True)

@event.listens_for(CashFlowDefinitionTotal.metadata, "after_create")
def create_views(target, connection, **kw):
    views_all(connection)