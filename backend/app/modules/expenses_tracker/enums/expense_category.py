from enum import Enum as PyEnum

class ExpenseCategory(str, PyEnum):
    REVOLUT = 'Revolut',
    IMAGIN = 'Imagin'