import { Component, OnInit, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, FormArray, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatSelectModule } from '@angular/material/select';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatNativeDateModule } from '@angular/material/core';
import { MatDividerModule } from '@angular/material/divider';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { ApiService, Customer, Product, Invoice } from '../../../core/services/api';

@Component({
  selector: 'app-invoice-form',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    RouterLink,
    MatCardModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatIconModule,
    MatSelectModule,
    MatDatepickerModule,
    MatNativeDateModule,
    MatDividerModule,
    MatTooltipModule,
    MatSnackBarModule
  ],
  templateUrl: './form.html',
  styleUrl: './form.scss'
})
export class FormComponent implements OnInit {
  form: FormGroup;
  isLoading = signal(false);
  isEditMode = signal(false);
  invoiceId: number | null = null;

  customers = signal<Customer[]>([]);
  products = signal<Product[]>([]);

  displayedColumns = ['position', 'description', 'quantity', 'unit', 'unit_price', 'vat_rate', 'line_total', 'actions'];

  formatChoices = [
    { value: 'zugferd', label: 'ZUGFeRD (PDF mit XML)' },
    { value: 'xrechnung', label: 'XRechnung (nur XML)' },
  ];

  unitChoices = [
    { value: 'HUR', label: 'Stunde' },
    { value: 'DAY', label: 'Tag' },
    { value: 'MON', label: 'Monat' },
    { value: 'C62', label: 'Pauschal' },
    { value: 'H87', label: 'Stück' },
    { value: 'KGM', label: 'Kilogramm' },
    { value: 'MTR', label: 'Meter' },
    { value: 'LTR', label: 'Liter' },
  ];

  vatRateChoices = [
    { value: '19.00', label: '19%' },
    { value: '7.00', label: '7%' },
    { value: '0.00', label: '0%' },
  ];

  constructor(
    private fb: FormBuilder,
    private apiService: ApiService,
    private router: Router,
    private route: ActivatedRoute,
    private snackBar: MatSnackBar
  ) {
    const today = new Date();
    const dueDate = new Date();
    dueDate.setDate(today.getDate() + 30);

    this.form = this.fb.group({
      customer: [null, Validators.required],
      format: ['zugferd', Validators.required],
      invoice_date: [today, Validators.required],
      due_date: [dueDate, Validators.required],
      leitweg_id: [''],
      buyer_reference: [''],
      notes: [''],
      payment_terms: ['Zahlbar innerhalb von 30 Tagen ohne Abzug.'],
      items: this.fb.array([])
    });
  }

  ngOnInit(): void {
    this.loadCustomers();
    this.loadProducts();

    const id = this.route.snapshot.paramMap.get('id');
    if (id && id !== 'new') {
      this.invoiceId = parseInt(id, 10);
      this.isEditMode.set(true);
      this.loadInvoice();
    } else {
      // Neue Rechnung: Eine leere Position hinzufügen
      this.addItem();
    }
  }

  get items(): FormArray {
    return this.form.get('items') as FormArray;
  }

  loadCustomers(): void {
    this.apiService.getCustomers().subscribe({
      next: (data: any) => {
        const customers = Array.isArray(data) ? data : (data.results || []);
        this.customers.set(customers);
      }
    });
  }

  loadProducts(): void {
    this.apiService.getProducts({ is_active: true }).subscribe({
      next: (data: any) => {
        const products = Array.isArray(data) ? data : (data.results || []);
        this.products.set(products);
      }
    });
  }

  loadInvoice(): void {
    if (!this.invoiceId) return;
    this.isLoading.set(true);
    this.apiService.getInvoice(this.invoiceId).subscribe({
      next: (invoice) => {
        this.form.patchValue({
          customer: invoice.customer,
          format: invoice.format,
          invoice_date: new Date(invoice.invoice_date),
          due_date: new Date(invoice.due_date),
          leitweg_id: invoice.leitweg_id,
          buyer_reference: invoice.buyer_reference,
          notes: invoice.notes,
          payment_terms: invoice.payment_terms
        });

        // Positionen laden
        this.items.clear();
        invoice.items.forEach(item => {
          this.items.push(this.fb.group({
            id: [item.id],
            product: [item.product],
            description: [item.description, Validators.required],
            quantity: [item.quantity, [Validators.required, Validators.min(0.001)]],
            unit: [item.unit, Validators.required],
            unit_price: [item.unit_price, [Validators.required, Validators.min(0)]],
            vat_rate: [item.vat_rate, Validators.required]
          }));
        });

        this.isLoading.set(false);
      },
      error: () => {
        this.snackBar.open('Fehler beim Laden', 'OK', { duration: 3000 });
        this.router.navigate(['/dashboard/invoices']);
      }
    });
  }

  addItem(): void {
    this.items.push(this.fb.group({
      id: [null],
      product: [null, Validators.required],
      description: [''],
      quantity: [1, [Validators.required, Validators.min(0.001)]],
      unit: ['H87'],
      unit_price: [0],
      vat_rate: ['19.00', Validators.required]
    }));
  }

  removeItem(index: number): void {
    if (this.items.length > 1) {
      this.items.removeAt(index);
    }
  }

  onProductSelect(index: number, productId: number): void {
    const product = this.products().find(p => p.id === productId);
    if (product) {
      const item = this.items.at(index);
      item.patchValue({
        description: product.name,
        unit: product.unit,
        unit_price: product.unit_price,
        vat_rate: product.vat_rate
      });
    }
  }

  onCustomerSelect(customerId: number): void {
    const customer = this.customers().find(c => c.id === customerId);
    if (customer) {
      this.form.patchValue({
        leitweg_id: customer.leitweg_id,
        due_date: this.calculateDueDate(customer.payment_terms_days)
      });

      // Bei Leitweg-ID automatisch XRechnung Format
      if (customer.leitweg_id) {
        this.form.patchValue({ format: 'xrechnung' });
      }
    }
  }

  calculateDueDate(days: number): Date {
    const date = new Date(this.form.get('invoice_date')?.value || new Date());
    date.setDate(date.getDate() + days);
    return date;
  }

  getLineTotal(index: number): number {
    const item = this.items.at(index);
    const quantity = parseFloat(item.get('quantity')?.value) || 0;
    const unitPrice = parseFloat(item.get('unit_price')?.value) || 0;
    return quantity * unitPrice;
  }

  getLineTax(index: number): number {
    const item = this.items.at(index);
    const vatRate = parseFloat(item.get('vat_rate')?.value) || 0;
    return this.getLineTotal(index) * (vatRate / 100);
  }

  getSubtotal(): number {
    let total = 0;
    for (let i = 0; i < this.items.length; i++) {
      total += this.getLineTotal(i);
    }
    return total;
  }

  getTotalTax(): number {
    let total = 0;
    for (let i = 0; i < this.items.length; i++) {
      total += this.getLineTax(i);
    }
    return total;
  }

  getTotal(): number {
    return this.getSubtotal() + this.getTotalTax();
  }

  getVatSummary(): { rate: string; net: number; tax: number }[] {
    const summary: { [key: string]: { net: number; tax: number } } = {};

    for (let i = 0; i < this.items.length; i++) {
      const item = this.items.at(i);
      const rate = item.get('vat_rate')?.value || '19.00';
      const lineNet = this.getLineTotal(i);
      const lineTax = this.getLineTax(i);

      if (!summary[rate]) {
        summary[rate] = { net: 0, tax: 0 };
      }
      summary[rate].net += lineNet;
      summary[rate].tax += lineTax;
    }

    return Object.entries(summary)
      .map(([rate, data]) => ({ rate, ...data }))
      .sort((a, b) => parseFloat(b.rate) - parseFloat(a.rate));
  }

  formatPrice(value: number): string {
    return new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' }).format(value);
  }

  getUnitLabel(unitCode: string): string {
    const unit = this.unitChoices.find(u => u.value === unitCode);
    return unit ? unit.label : unitCode;
  }

  onSubmit(): void {
    if (this.form.invalid || this.items.length === 0) {
      this.snackBar.open('Bitte alle Pflichtfelder ausfüllen', 'OK', { duration: 3000 });
      return;
    }

    this.isLoading.set(true);

    const formValue = this.form.value;
    const invoiceData = {
      customer: formValue.customer,
      format: formValue.format,
      invoice_date: this.formatDate(formValue.invoice_date),
      due_date: this.formatDate(formValue.due_date),
      leitweg_id: formValue.leitweg_id,
      buyer_reference: formValue.buyer_reference,
      notes: formValue.notes,
      payment_terms: formValue.payment_terms
    };

    if (this.isEditMode()) {
      this.apiService.updateInvoice(this.invoiceId!, invoiceData).subscribe({
        next: () => {
          this.snackBar.open('Rechnung aktualisiert', 'OK', { duration: 2000 });
          this.router.navigate(['/dashboard/invoices']);
        },
        error: () => {
          this.snackBar.open('Fehler beim Speichern', 'OK', { duration: 3000 });
          this.isLoading.set(false);
        }
      });
    } else {
      this.apiService.createInvoice(invoiceData).subscribe({
        next: (invoice) => {
          // Positionen speichern
          this.saveItems(invoice.id);
        },
        error: () => {
          this.snackBar.open('Fehler beim Speichern', 'OK', { duration: 3000 });
          this.isLoading.set(false);
        }
      });
    }
  }

  private saveItems(invoiceId: number): void {
    const items = this.items.value;
    let savedCount = 0;

    items.forEach((item: any) => {
      this.apiService.createInvoiceItem({
        invoice: invoiceId,
        product: item.product,
        description: item.description,
        quantity: item.quantity,
        unit: item.unit,
        unit_price: item.unit_price,
        vat_rate: item.vat_rate
      }).subscribe({
        next: () => {
          savedCount++;
          if (savedCount === items.length) {
            this.snackBar.open('Rechnung erstellt', 'OK', { duration: 2000 });
            this.router.navigate(['/dashboard/invoices']);
          }
        },
        error: () => {
          this.snackBar.open('Fehler beim Speichern der Positionen', 'OK', { duration: 3000 });
          this.isLoading.set(false);
        }
      });
    });
  }

  private formatDate(date: Date): string {
    return date.toISOString().split('T')[0];
  }
}
