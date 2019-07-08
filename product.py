# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from decimal import Decimal

from trytond import backend
from trytond.i18n import gettext
from trytond.model import ModelView, fields
from trytond.wizard import Wizard, StateView, StateTransition, Button
from trytond.pyson import Eval
from trytond.transaction import Transaction
from trytond.pool import Pool, PoolMeta

from trytond.modules.account_product.product import (
    account_used, template_property)
from trytond.modules.product import price_digits
from .exceptions import ModifyCostPriceError

__all__ = ['Category', 'CategoryAccount', 'Template',
    'Product', 'ModifyCostPriceAsk',
    'ModifyCostPriceShowMove', 'ModifyCostPrice']
account_names = [
    'account_stock', 'account_stock_supplier', 'account_stock_customer',
    'account_stock_production', 'account_stock_lost_found']


class Category(metaclass=PoolMeta):
    __name__ = 'product.category'
    account_stock = fields.MultiValue(fields.Many2One(
            'account.account', "Account Stock",
            domain=[
                ('type.stock', '=', True),
                ('company', '=', Eval('context', {}).get('company', -1)),
                ],
            states={
                'invisible': (~Eval('context', {}).get('company')
                    | Eval('account_parent')
                    | ~Eval('accounting', False)),
                },
            depends=['account_parent', 'accounting']))
    account_stock_supplier = fields.MultiValue(fields.Many2One(
            'account.account', "Account Stock Supplier",
            domain=[
                ('type.stock', '=', True),
                ('company', '=', Eval('context', {}).get('company', -1)),
                ],
            states={
                'invisible': (~Eval('context', {}).get('company')
                    | Eval('account_parent')
                    | ~Eval('accounting', False)),
                },
            depends=['account_parent', 'accounting']))
    account_stock_customer = fields.MultiValue(fields.Many2One(
            'account.account', "Account Stock Customer",
            domain=[
                ('type.stock', '=', True),
                ('company', '=', Eval('context', {}).get('company', -1)),
                ],
            states={
                'invisible': (~Eval('context', {}).get('company')
                    | Eval('account_parent')
                    | ~Eval('accounting', False)),
                },
            depends=['account_parent', 'accounting']))
    account_stock_production = fields.MultiValue(fields.Many2One(
            'account.account', "Account Stock Production",
            domain=[
                ('type.stock', '=', True),
                ('company', '=', Eval('context', {}).get('company', -1)),
                ],
            states={
                'invisible': (~Eval('context', {}).get('company')
                    | Eval('account_parent')
                    | ~Eval('accounting', False)),
                },
            depends=['account_parent', 'accounting']))
    account_stock_lost_found = fields.MultiValue(fields.Many2One(
            'account.account', "Account Stock Lost and Found",
            domain=[
                ('type.stock', '=', True),
                ('company', '=', Eval('context', {}).get('company', -1)),
                ],
            states={
                'invisible': (~Eval('context', {}).get('company')
                    | Eval('account_parent')
                    | ~Eval('accounting', False)),
                },
            depends=['account_parent', 'accounting']))

    @classmethod
    def multivalue_model(cls, field):
        pool = Pool()
        if field in account_names:
            return pool.get('product.category.account')
        return super(Category, cls).multivalue_model(field)

    @property
    @account_used('account_stock')
    def account_stock_used(self):
        pass

    @property
    @account_used('account_stock_supplier')
    def account_stock_supplier_used(self):
        pass

    @property
    @account_used('account_stock_customer')
    def account_stock_customer_used(self):
        pass

    @property
    @account_used('account_stock_production')
    def account_stock_production_used(self):
        pass

    @property
    @account_used('account_stock_lost_found')
    def account_stock_lost_found_used(self):
        pass


class CategoryAccount(metaclass=PoolMeta):
    __name__ = 'product.category.account'
    account_stock = fields.Many2One(
        'account.account', "Account Stock",
        domain=[
            ('type.stock', '=', True),
            ('type.statement', '=', 'balance'),
            ('company', '=', Eval('company', -1)),
            ],
        depends=['company'])
    account_stock_supplier = fields.Many2One(
        'account.account', "Account Stock Supplier",
        domain=[
            ('type.stock', '=', True),
            ('type.statement', '=', 'income'),
            ('company', '=', Eval('company', -1)),
            ],
        depends=['company'])
    account_stock_customer = fields.Many2One(
        'account.account', "Account Stock Customer",
        domain=[
            ('type.stock', '=', True),
            ('type.statement', '=', 'income'),
            ('company', '=', Eval('company', -1)),
            ],
        depends=['company'])
    account_stock_production = fields.Many2One(
        'account.account', "Account Stock Production",
        domain=[
            ('type.stock', '=', True),
            ('type.statement', '=', 'income'),
            ('company', '=', Eval('company', -1)),
            ],
        depends=['company'])
    account_stock_lost_found = fields.Many2One(
        'account.account', "Account Stock Lost and Found",
        domain=[
            ('type.stock', '=', True),
            ('type.statement', '=', 'income'),
            ('company', '=', Eval('company', -1)),
            ],
        depends=['company'])

    @classmethod
    def __register__(cls, module_name):
        TableHandler = backend.get('TableHandler')
        exist = TableHandler.table_exist(cls._table)
        if exist:
            table = cls.__table_handler__(module_name)
            exist &= all(table.column_exist(c) for c in account_names)

        super(CategoryAccount, cls).__register__(module_name)

        if not exist:
            # Re-migration
            cls._migrate_property([], [], [])

    @classmethod
    def _migrate_property(cls, field_names, value_names, fields):
        field_names.extend(account_names)
        value_names.extend(account_names)
        super(CategoryAccount, cls)._migrate_property(
            field_names, value_names, fields)


class Template(metaclass=PoolMeta):
    __name__ = 'product.template'

    @classmethod
    def __setup__(cls):
        super(Template, cls).__setup__()
        cls._modify_no_move.append(
            ('cost_price',
                'account_stock_continental.msg_product_change_cost_price'))

    @property
    @account_used('account_stock', 'account_category')
    def account_stock_used(self):
        pass

    @property
    @account_used('account_stock_supplier', 'account_category')
    def account_stock_supplier_used(self):
        pass

    @property
    @account_used('account_stock_customer', 'account_category')
    def account_stock_customer_used(self):
        pass

    @property
    @account_used('account_stock_production', 'account_category')
    def account_stock_production_used(self):
        pass

    @property
    @account_used('account_stock_lost_found', 'account_category')
    def account_stock_lost_found_used(self):
        pass


class Product(metaclass=PoolMeta):
    __name__ = 'product.product'
    account_stock_used = template_property('account_stock_used')
    account_stock_supplier_used = template_property(
        'account_stock_supplier_used')
    account_stock_customer_used = template_property(
        'account_stock_customer_used')
    account_stock_production_used = template_property(
        'account_stock_production_used')
    account_stock_lost_found_used = template_property(
        'account_stock_lost_found_used')


class ModifyCostPriceAsk(ModelView):
    'Modify Cost Price Ask'
    __name__ = 'product.modify_cost_price.ask'
    template = fields.Many2One('product.template', 'Product', readonly=True,
        states={
            'invisible': ~Eval('template'),
            })
    product = fields.Many2One('product.product', 'Variant', readonly=True,
        states={
            'invisible': ~Eval('product'),
            })
    cost_price = fields.Numeric('Cost Price', required=True,
        digits=price_digits)


class ModifyCostPriceShowMove(ModelView):
    'Modify Cost Price Show Move'
    __name__ = 'product.modify_cost_price.show_move'
    price_difference = fields.Numeric('Price Difference', readonly=True,
        digits=price_digits)
    amount = fields.Numeric('Amount', readonly=True,
        digits=(16, Eval('currency_digits', 2)), depends=['currency_digits'])
    currency_digits = fields.Integer('Currency Digits', readonly=True)
    journal = fields.Many2One('account.journal', 'Journal', required=True)
    stock_account = fields.Many2One('account.account', 'Stock Account',
        readonly=True)
    counterpart = fields.Many2One('account.account', 'Counterpart',
        domain=[
            ('company', 'in',
                [Eval('context', {}).get('company', -1), None]),
            ('id', '!=', Eval('stock_account')),
            ('type.stock', '=', True),
            ],
        depends=['stock_account'], required=True)
    description = fields.Char('Description')


class ModifyCostPrice(Wizard):
    'Modify Cost Price'
    __name__ = 'product.modify_cost_price'
    start_state = 'ask_price'
    ask_price = StateView('product.modify_cost_price.ask',
        'account_stock_continental.modify_cost_price_ask_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('OK', 'should_show_move', 'tryton-forward', default=True),
            ])
    should_show_move = StateTransition()
    show_move = StateView('product.modify_cost_price.show_move',
        'account_stock_continental.modify_cost_price_show_move_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('OK', 'create_move', 'tryton-ok', default=True),
            ])
    create_move = StateTransition()
    modify_price = StateTransition()

    def default_ask_price(self, fields):
        pool = Pool()
        Product = pool.get('product.product')

        context = Transaction().context
        default = {}
        product = Product(context['active_id'])
        default['product'] = product.id
        default['cost_price'] = getattr(
            product, 'recompute_cost_price_%s' % product.cost_price_method)()
        return default

    @staticmethod
    def get_product():
        'Return the product instance'
        pool = Pool()
        Product = pool.get('product.product')
        context = Transaction().context
        return Product(context['active_id'])

    @classmethod
    def get_quantity(cls):
        pool = Pool()
        Date = pool.get('ir.date')
        Stock = pool.get('stock.location')

        locations = Stock.search([('type', '=', 'storage')])
        stock_date_end = Date.today()
        with Transaction().set_context(locations=[l.id for l in locations],
                stock_date_end=stock_date_end):
            product = cls.get_product()
            return product.quantity

    def transition_should_show_move(self):
        if self.get_quantity() != 0:
            return 'show_move'
        return 'modify_price'

    def default_show_move(self, fields):
        pool = Pool()
        User = pool.get('res.user')
        AccountConfiguration = pool.get('account.configuration')

        product = self.get_product()
        price_diff = (self.ask_price.cost_price
                - product.cost_price)
        user = User(Transaction().user)
        amount = user.company.currency.round(
            Decimal(str(self.get_quantity())) * price_diff)
        stock_account_id = product.account_stock_used.id
        config = AccountConfiguration(1)
        stock_journal_id = config.stock_journal.id
        counterpart_id = (config.cost_price_counterpart_account.id if
            config.cost_price_counterpart_account else None)
        return {
            'journal': stock_journal_id,
            'amount': amount,
            'price_difference': price_diff,
            'stock_account': stock_account_id,
            'counterpart': counterpart_id,
            'currency_digits': user.company.currency.digits,
            }

    def get_move_lines(self):
        Line = Pool().get('account.move.line')
        amount = self.show_move.amount
        return [Line(
                debit=amount if amount > 0 else 0,
                credit=-amount if amount < 0 else 0,
                account=self.show_move.stock_account,
                ),
            Line(
                debit=-amount if amount < 0 else 0,
                credit=amount if amount > 0 else 0,
                account=self.show_move.counterpart,
                ),
            ]

    def get_move(self):
        pool = Pool()
        Date = pool.get('ir.date')
        Period = pool.get('account.period')
        User = pool.get('res.user')
        Move = pool.get('account.move')

        user = User(Transaction().user)
        period_id = Period.find(user.company.id)
        return Move(
            description=self.show_move.description,
            period=period_id,
            journal=self.show_move.journal,
            date=Date.today(),
            origin=self.get_product(),
            lines=self.get_move_lines(),
            )

    def transition_create_move(self):
        Move = Pool().get('account.move')

        if self.show_move.counterpart == self.show_move.stock_account:
            raise ModifyCostPriceError(
                gettext('account_stock_continental'
                    '.msg_modify_cost_price_same_account',
                    account=self.show_move.counterpart.rec_name))
        move = self.get_move()
        move.save()
        Move.post([move])
        return 'modify_price'

    def transition_modify_price(self):
        self.ask_price.product.set_multivalue(
            'cost_price', self.ask_price.cost_price)
        return 'end'
