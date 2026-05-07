from datetime import date
from decimal import Decimal

from django.test import SimpleTestCase

from .forms import PaymentForm, PolicyForm


class PolicyFormTests(SimpleTestCase):
    def test_requires_fixed_deductible_when_type_is_fixed(self):
        form = PolicyForm()
        form.cleaned_data = {
            'deductible_type': 'FIXED',
            'fixed_deductible': None,
            'percentage_deductible': Decimal('10.00'),
        }
        cleaned = form.clean()

        self.assertIn('fixed_deductible', form.errors)
        self.assertIsNone(cleaned['percentage_deductible'])

    def test_clears_fixed_deductible_when_percentage_type(self):
        form = PolicyForm()
        form.cleaned_data = {
            'deductible_type': 'PERCENTAGE',
            'fixed_deductible': Decimal('1000.00'),
            'percentage_deductible': Decimal('10.00'),
        }
        cleaned = form.clean()

        self.assertIsNone(cleaned['fixed_deductible'])


class PaymentFormTests(SimpleTestCase):
    def test_payable_requires_creditor(self):
        form = PaymentForm(data={
            'direction': 'PAYABLE',
            'origin': 'OTHER',
            'description': 'Pagamento teste',
            'amount': '100.00',
            'paid_amount': '0.00',
            'due_date': date.today(),
            'paid_date': '',
            'status': 'PENDING',
            'creditor_name': '',
        })

        self.assertFalse(form.is_valid())
        self.assertIn('creditor_name', form.errors)

    def test_paid_amount_cannot_exceed_amount(self):
        form = PaymentForm(data={
            'direction': 'RECEIVABLE',
            'origin': 'PREMIUM',
            'description': 'Receita teste',
            'amount': '100.00',
            'paid_amount': '120.00',
            'due_date': date.today(),
            'paid_date': date.today(),
            'status': 'PAID',
            'creditor_name': '',
        })

        self.assertFalse(form.is_valid())
        self.assertIn('paid_amount', form.errors)
