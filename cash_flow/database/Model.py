from sqlalchemy import Integer, String, DateTime, Numeric, ForeignKey, event, \
    text, Boolean, Float, UniqueConstraint, PrimaryKeyConstraint, BigInteger
from sqlalchemy.orm import DeclarativeBase, mapped_column, relationship


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
    TILDES_JUMIS = 2
    id = mapped_column(Integer, primary_key=True)
    type_id = mapped_column(ForeignKey("A03_SourceTypes.id", ondelete="CASCADE"))
    name = mapped_column(String(100), nullable=False)
    url = mapped_column(String(255), nullable=False)
    database = mapped_column(String(100), nullable=True)
    username = mapped_column(String(100), nullable=True)
    password = mapped_column(String(255), nullable=True)


@event.listens_for(Source.metadata, "after_create")
def default_data_sources(target, connection, **kw):
    table_name = Source.__tablename__
    sql = ("INSERT INTO " + table_name +
           " (id, type_id, name, url, database, username, password) " +
           " VALUES (:id, :type, :name, :url, :database, :username, :password)")
    params = [{ "id": Source.GENIE,
                "type": SourceType.GENIE,
                "name": "Genie Cash Flow App",
                "url": "localhost",
                "database": None,
                "username": "user",
                "password": "password"
                },
                {"id": Source.TILDES_JUMIS,
               "type": SourceType.TILDES_JUMIS,
               "name": "Tildes Jumis galvenā db",
               "url": "jumiscloud.mansjumis.lv,12878",
               "database": "alfreds",
               "username": "genie@inbox.lv",
               "password": "fisJMLfHsto7q-C!^7(J[5G7VHfTj7"},
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
              ]

    connection.execute(text(sql), params)


class Partner(Base):
    __tablename__ = "B04_Partners"
    id = mapped_column(Integer, primary_key=True)
    name = mapped_column(String(100), nullable=False)
    cr_priority = mapped_column(Integer, nullable=False, default=100)
    cr_void = mapped_column(Boolean, nullable=False, default=False)
    dr_priority = mapped_column(Integer, nullable=False, default=100)
    dr_void = mapped_column(Boolean, nullable=False, default=False)

class Document(Base):
    __tablename__ = "D01_Documents"

    id = mapped_column(Integer, primary_key=True)
    type_id = mapped_column(ForeignKey("D02_DocTypes.id"))
    number = mapped_column(String(30), nullable=True)
    date = mapped_column(DateTime, nullable=False, index=True)
    date_due = mapped_column(DateTime, nullable=True, index=True)
    partner_id = mapped_column(ForeignKey("B04_Partners.id"), nullable=False)
    description = mapped_column(String(255), nullable=True)
    currency = mapped_column(ForeignKey("B01_Currencies.code"), nullable=False, index=True)
    amount = mapped_column(Numeric(12, 2, 2), nullable=False)
    amount_LC = mapped_column(Numeric(12, 2, 2), nullable=False)
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
    BANK_RECEIPT = 14
    BANK_PAYMENT = 13
    INVOICE_CUSTOMER = 104
    INVOICE_VENDOR = 103
    GL_TRANSACTIONS = 6
    id = mapped_column(Integer, primary_key=True)
    name = mapped_column(String(100))



class GeneralLedger(Base):
    __tablename__ = "D03_GeneralLedger"
    id = mapped_column(Integer, primary_key=True)
    document_id = mapped_column(ForeignKey("D01_Documents.id", ondelete="CASCADE"), nullable=False)
    date = mapped_column(DateTime, nullable=False, index=True)
    date_due = mapped_column(DateTime, nullable=True, index=True)
    partner_id = mapped_column(ForeignKey("B04_Partners.id"), nullable=False, index=True)
    entry_type = mapped_column(String(2), nullable=False, index=True)
    account = mapped_column(ForeignKey("B02_Accounts.code"), nullable=False, index=True)
    currency =mapped_column(ForeignKey("B01_Currencies.code"), nullable=False, index=True)
    amount = mapped_column(Numeric(12,2, 2), nullable=False)
    amount_LC = mapped_column(Numeric(12,2, 2), nullable=False)
    cleared = mapped_column(Boolean, nullable=False, server_default=text("0"))
    cleared_amount = mapped_column(Numeric(12, 2), nullable=False, server_default=text("0"))
    date_cleared = mapped_column(DateTime, nullable=True, index=True)
    document = relationship("Document", back_populates="gl")

    __table_args__ = (UniqueConstraint("document_id", "partner_id", "account", "currency"),)



class GeneralLedger_preserved(Base):
    __tablename__ = "D03_GeneralLedger_preserved"
    id = mapped_column(Integer, primary_key=True)
    document_id = mapped_column(ForeignKey("D01_Documents.id"), nullable=False)
    date_planned_clearing = mapped_column(DateTime, nullable=True, index=True)
    partner_id = mapped_column(ForeignKey("B04_Partners.id"), nullable=False, index=True)
    account = mapped_column(ForeignKey("B02_Accounts.code"), nullable=False, index=True)
    currency = mapped_column(ForeignKey("B01_Currencies.code"), nullable=False, index=True)
    memo = mapped_column(String)
    void = mapped_column(Boolean, nullable=False, server_default=text("0"))
    priority = mapped_column(Integer, nullable=False, server_default=text("100"))

    __table_args__ = (UniqueConstraint("document_id", "partner_id", "account", "currency"),)


class Reconciliation(Base):
    __tablename__ = "D04_Reconciliations"
    id = mapped_column(Integer, primary_key=True)
    date = mapped_column(DateTime, nullable=False)
    account = mapped_column(ForeignKey("B02_Accounts.code"), nullable=False, index=True)
    currency = mapped_column(ForeignKey("B01_Currencies.code"), nullable=False, index=True)
    amount = mapped_column(Numeric(12,2), nullable=False)
    cr_docid = mapped_column(ForeignKey("D01_Documents.id", ondelete="CASCADE"), nullable=False)
    dr_docid = mapped_column(ForeignKey("D01_Documents.id", ondelete="CASCADE"), nullable=False)


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
def default_data_cf_definition(target, connection, **kw):
    table_name = CashFlowDefinition.__tablename__
    sql = "INSERT INTO " + table_name + " (id, key, definition_type, name) VALUES (:id, :key, :type, :name)"
    params = [{"id": 1, "key": "100", "type": None, "name": "PAMATDARBĪBAS NAUDAS PLŪSMA"},
              {"id": 2, "key": "101", "type": 1, "name": "Ieņēmumi no preču un pakalpojumu pārdošanas"},
              {"id": 3, "key": "102", "type": 1, "name": "Maksājumi piegādātājiem"},
              {"id": 4, "key": "103", "type": 1, "name": "Maksājumi darbiniekiem"},
              {"id": 5, "key": "104", "type": 1, "name": "Pārējie pamatdarbības ieņēmumi un izdevumi"},
              {"id": 6, "key": "199", "type": 2, "name": "BRUTO PAMATDARBĪBAS NAUDAS PLŪSMA"},
              {"id": 7, "key": "201", "type": 1, "name": "Izdevumi procentu maksājumiem"},
              {"id": 8, "key": "202", "type": 1, "name": "Izdevumi nodokļu maksājumiem"},
              {"id": 9, "key": "203", "type": 1, "name": "Naudas plūsma no ārkārtas posteņiem"},
              {"id": 10, "key": "299", "type": 2, "name": "PAMATDARBĪBAS NETO NAUDAS PLŪSMA"},
              {"id": 11, "key": "300", "type": None, "name": "IEGULDĪŠANAS DARBĪBAS NAUDAS PLŪSMA"},
              {"id": 12, "key": "301", "type": 1, "name": "Radniecīgo vai asociēto uzņēmumu daļu iegāde"},
              {"id": 13, "key": "302", "type": 1, "name": "Ieņēmumi no radniecīgo vai asociēto uzņēmumu daļu pārdošanas"},
              {"id": 14, "key": "303", "type": 1, "name": "Pamatlīdzekļu un nemateriālo ieguldījumu iegāde"},
              {"id": 15, "key": "304", "type": 1, "name": "Ieņēmumi no pamatlīdzekļu un nemateriālo ieguldījumu pārdošanas"},
              {"id": 16, "key": "305", "type": 1, "name": "Izsniegtie aizdevumi"},
              {"id": 17, "key": "306", "type": 1, "name": "Ieņēmumi no aizdevumu atmaksas"},
              {"id": 18, "key": "307", "type": 1, "name": "Saņemtie procenti"},
              {"id": 19, "key": "308", "type": 1, "name": "Saņemtās dividendes"},
              {"id": 20, "key": "309", "type": 2, "name": "IEGULDĪJUMU DARBĪBAS NETO NAUDAS PLŪSMA"},
              {"id": 21, "key": "400", "type": None, "name": "FINANSĒŠANAS DARBĪBAS NAUDAS PLŪSMA"},
              {"id": 22, "key": "401", "type": 1, "name": "Ieņēmumi no akciju vai obligāciju emisijas"},
              {"id": 23, "key": "402", "type": 1, "name": "Saņemtie aizņēmumi"},
              {"id": 24, "key": "403", "type": 1, "name": "Izdevumi aizdevumu atmaksai"},
              {"id": 25, "key": "404", "type": 1, "name": "Samaksātie procenti"},
              {"id": 26, "key": "405", "type": 1, "name": "Izmaksātās dividendes"},
              {"id": 27, "key": "499", "type": 2, "name": "FINANSĒŠANAS DARBĪBAS NETO NAUDAS PLŪSMA"},
              {"id": 28, "key": "901", "type": 1, "name": "Ārvalstu valūtu kursu svārstību rezultāts"},
              {"id": 29, "key": "902", "type": 2, "name": "NETO NAUDAS PLŪSMA"},
              {"id": 30, "key": "999", "type": 3, "name": "NAUDAS LĪDZEKĻU ATLIKUMS PĀRSKATA PERIODA BEIGĀS"}
              ]

    connection.execute(text(sql), params)

class CashFlowDefinitionAccount(Base):
    __tablename__ = "E01_CashFlowDefinitionAccounts"
    id = mapped_column(Integer, primary_key=True)
    definition_id = mapped_column(ForeignKey("E01_CashFlowDefinition.id"), nullable=True)
    cash_type = mapped_column(String(10), nullable=True)
    account = mapped_column(ForeignKey("B02_Accounts.code"), nullable=True)

class CashFlowDefinitionTotal(Base):
    __tablename__ = "E01_CashFlowDefinitionTotals"
    id = mapped_column(Integer, primary_key=True)
    definition_id = mapped_column(ForeignKey("E01_CashFlowDefinition.id"), nullable=True)
    definition_summarized = mapped_column(ForeignKey("E01_CashFlowDefinition.id"), nullable=True)

@event.listens_for(CashFlowDefinitionTotal.metadata, "after_create")
def default_data_cf_totals(target, connection, **kw):
    table_name = CashFlowDefinitionTotal.__tablename__
    sql = "INSERT INTO " + table_name + " (definition_id, definition_summarized) VALUES (:id, :sum)"
    params = [
              # BRUTO PAMATDARBĪBAS NAUDAS PLŪSMA
                  {"id": 6, "sum": 2},
                  {"id": 6, "sum": 3},
                  {"id": 6, "sum": 4},
                  {"id": 6, "sum": 5},
              # PAMATDARBĪBAS NETO NAUDAS PLŪSMA
                  {"id": 10, "sum": 2},
                  {"id": 10, "sum": 3},
                  {"id": 10, "sum": 4},
                  {"id": 10, "sum": 5},
                  {"id": 10, "sum": 7},
                  {"id": 10, "sum": 8},
                  {"id": 10, "sum": 9},
              # IEGULDĪJUMU DARBĪBAS NETO NAUDAS PLŪSMA
                    {"id": 20, "sum": 12},
                    {"id": 20, "sum": 13},
                    {"id": 20, "sum": 14},
                    {"id": 20, "sum": 15},
                    {"id": 20, "sum": 16},
                    {"id": 20, "sum": 17},
                    {"id": 20, "sum": 18},
                    {"id": 20, "sum": 19},
              # FINANSĒŠANAS DARBĪBAS NETO NAUDAS PLŪSMA
                {"id": 27, "sum": 22},
                {"id": 27, "sum": 23},
                {"id": 27, "sum": 24},
                {"id": 27, "sum": 25},
                {"id": 27, "sum": 26},
              # NETO NAUDAS PLŪSMA
                {"id": 29, "sum": 2},
                {"id": 29, "sum": 3},
                {"id": 29, "sum": 4},
                {"id": 29, "sum": 5},
                {"id": 29, "sum": 7},
                {"id": 29, "sum": 8},
                {"id": 29, "sum": 9},
                {"id": 29, "sum": 12},
                {"id": 29, "sum": 13},
                {"id": 29, "sum": 14},
                {"id": 29, "sum": 15},
                {"id": 29, "sum": 16},
                {"id": 29, "sum": 17},
                {"id": 29, "sum": 18},
                {"id": 29, "sum": 19},
                {"id": 29, "sum": 22},
                {"id": 29, "sum": 23},
                {"id": 29, "sum": 24},
                {"id": 29, "sum": 25},
                {"id": 29, "sum": 26},
                {"id": 29, "sum": 28}
    ]

    connection.execute(text(sql), params)


class BudgetEntry(Base):
    __tablename__ = "F01_BudgetEntries"
    id = mapped_column(Integer, primary_key=True)
    definition_id = mapped_column(ForeignKey("E01_CashFlowDefinition.id"), nullable=False)
    cash_type = mapped_column(String(10), nullable=True, index=True)
    date = mapped_column(DateTime, nullable=True, index=True)
    amount_LC = mapped_column(Numeric(12, 2, 2), nullable=True)
    memo = mapped_column(String(250), nullable=True)

class Jumis_Account(Base):
    __tablename__ = "Jumis_Account"
    AccountID = mapped_column(Integer, primary_key=True)
    AccountCode = mapped_column(String(21), nullable=True, index=True)
    AccountName = mapped_column(String(50), nullable=True)
    CreateDate = mapped_column(DateTime, nullable=True, index=True)
    UpdateDate = mapped_column(DateTime, nullable=True, index=True)
    rn = mapped_column(Integer)

class Jumis_Partner(Base):
    __tablename__ = "Jumis_Partner"
    PartnerID = mapped_column(Integer, primary_key=True)
    PartnerName = mapped_column(String(255), nullable=False)
    PhysicalPersonFirstName = mapped_column(String(255), nullable=True)
    CreateDate = mapped_column(DateTime, nullable=True, index=True)
    UpdateDate = mapped_column(DateTime, nullable=True, index=True)
    rn = mapped_column(Integer)

class Jumis_Currency(Base):
    __tablename__ = "Jumis_Currency"
    CurrencyID = mapped_column(Integer, primary_key=True)
    CurrencyCode = mapped_column(String(21), nullable=False, index=True)
    Description = mapped_column(String(255), nullable=True)
    rn = mapped_column(Integer)

class Jumis_CurrencyRates(Base):
    __tablename__ = "Jumis_CurrencyRates"
    RateID = mapped_column(Integer, primary_key=True)
    CurrencyID = mapped_column(ForeignKey("Jumis_Currency.CurrencyID"), nullable=False)
    RateDate = mapped_column(DateTime, nullable=False, index=True)
    Rate = mapped_column(Numeric(15, 10, 10), nullable=True)
    rn = mapped_column(Integer)

class Jumis_DocumentType(Base):
    __tablename__ = "Jumis_DocumentType"
    DocumentTypeID = mapped_column(Integer, primary_key=True)
    TypeName = mapped_column(String(255), nullable=True)
    TypeShortName = mapped_column(String(255), nullable=True)
    rn = mapped_column(Integer)

class Jumis_FinancialDoc(Base):
    __tablename__ = "Jumis_FinancialDoc"
    FinancialDocID = mapped_column(Integer, primary_key=True)
    FinancialDocNo = mapped_column(String(50), nullable=True)
    DocumentTypeID = mapped_column(Integer, nullable=False, index=True)
    FinancialDocDate = mapped_column(DateTime, nullable=False, index=True)
    DocStatus = mapped_column(Integer, nullable=False, index=True)
    DocCurrencyID = mapped_column(Integer, nullable=False, index=True)
    DocAmount = mapped_column(Numeric(12, 2, 2), nullable=True)
    PartnerID = mapped_column(Integer, nullable=False, index=True)
    DisbursementTerm = mapped_column(DateTime, nullable=True, index=True)
    Disbursement = mapped_column(Integer, nullable=True, index=True)
    DisbursementDate = mapped_column(DateTime, nullable=True, index=True)
    Comments = mapped_column(String(255), nullable=True)
    DocRegDate = mapped_column(DateTime, nullable=True, index=True)
    CreateDate = mapped_column(DateTime, nullable=True, index=True)
    UpdateDate = mapped_column(DateTime, nullable=True, index=True)
    rn = mapped_column(Integer)

class Jumis_FinancialDocLine(Base):
    __tablename__ = "Jumis_FinancialDocLine"
    FinancialDocLineID = mapped_column(Integer, primary_key=True)
    FinancialDocID = mapped_column(ForeignKey("Jumis_FinancialDoc"), nullable=False)
    LineDate = mapped_column(DateTime, nullable=False, index=True)
    CurrencyID = mapped_column(Integer, nullable=False, index=True)
    Amount = mapped_column(Numeric(12, 2, 2), nullable=True)
    DebetID = mapped_column(Integer, nullable=False, index=True)
    CreditID = mapped_column(Integer, nullable=False, index=True)
    Comments = mapped_column(String(255), nullable=True)
    DisbursementDocID = mapped_column(Integer, nullable=True, index=True)
    UpdateDate = mapped_column(DateTime, nullable=True, index=True)
    CreateDate = mapped_column(DateTime, nullable=True, index=True)
    rn = mapped_column(Integer)

class Jumis_FinancialDocDisbursement(Base):
    __tablename__ = "Jumis_FinancialDocDisbursement"
    FinancialDocDisbursementID = mapped_column(Integer, primary_key=True)
    DebetDocID = mapped_column(Integer, nullable=False, index=True)
    CreditDocID = mapped_column(Integer, nullable=False, index=True)
    DebetAmount = mapped_column(Numeric(12, 2, 2), nullable=True)
    CreditAmount = mapped_column(Numeric(12, 2, 2), nullable=True)
    rn = mapped_column(Integer)



