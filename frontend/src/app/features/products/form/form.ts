import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatSelectModule } from '@angular/material/select';
import { MatRadioModule } from '@angular/material/radio';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatDividerModule } from '@angular/material/divider';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { ApiService, Product } from '../../../core/services/api';

@Component({
  selector: 'app-product-form',
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
    MatRadioModule,
    MatCheckboxModule,
    MatDividerModule,
    MatSnackBarModule
  ],
  templateUrl: './form.html',
  styleUrl: './form.scss'
})
export class FormComponent implements OnInit {
  form: FormGroup;
  isLoading = signal(false);
  isEditMode = signal(false);
  productId: number | null = null;

  // UN/CEFACT Einheiten (wie im Backend)
  unitChoices = [
    { value: 'HUR', label: 'Stunde', type: 'service' },
    { value: 'DAY', label: 'Tag', type: 'service' },
    { value: 'MON', label: 'Monat', type: 'service' },
    { value: 'C62', label: 'Pauschal', type: 'service' },
    { value: 'H87', label: 'Stück', type: 'product' },
    { value: 'KGM', label: 'Kilogramm', type: 'product' },
    { value: 'MTR', label: 'Meter', type: 'product' },
    { value: 'LTR', label: 'Liter', type: 'product' },
  ];

  vatRateChoices = [
    { value: '19.00', label: '19% (Standard)' },
    { value: '7.00', label: '7% (Ermäßigt)' },
    { value: '0.00', label: '0% (Steuerfrei)' },
  ];

  productType = signal<'service' | 'product'>('service');

  constructor(
    private fb: FormBuilder,
    private apiService: ApiService,
    private router: Router,
    private route: ActivatedRoute,
    private snackBar: MatSnackBar
  ) {
    this.form = this.fb.group({
      name: ['', Validators.required],
      description: [''],
      unit: ['HUR', Validators.required],
      unit_price: ['', [Validators.required, Validators.min(0)]],
      vat_rate: ['19.00', Validators.required],
      is_active: [true]
    });
  }

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (id && id !== 'new') {
      this.productId = parseInt(id, 10);
      this.isEditMode.set(true);
      this.loadProduct();
    }
  }

  loadProduct(): void {
    if (!this.productId) return;
    this.isLoading.set(true);
    this.apiService.getProduct(this.productId).subscribe({
      next: (product) => {
        this.form.patchValue(product);
        // Produkttyp anhand der Einheit setzen
        const unit = this.unitChoices.find(u => u.value === product.unit);
        if (unit) {
          this.productType.set(unit.type as 'service' | 'product');
        }
        this.isLoading.set(false);
      },
      error: () => {
        this.snackBar.open('Fehler beim Laden', 'OK', { duration: 3000 });
        this.router.navigate(['/dashboard/products']);
      }
    });
  }

  onProductTypeChange(type: 'service' | 'product'): void {
    this.productType.set(type);
    // Standardeinheit setzen
    const defaultUnit = type === 'service' ? 'HUR' : 'H87';
    this.form.patchValue({ unit: defaultUnit });
  }

  getFilteredUnits() {
    return this.unitChoices.filter(u => u.type === this.productType());
  }

  onSubmit(): void {
    if (this.form.invalid) return;

    this.isLoading.set(true);
    const data = this.form.value;

    const request = this.isEditMode()
      ? this.apiService.updateProduct(this.productId!, data)
      : this.apiService.createProduct(data);

    request.subscribe({
      next: () => {
        this.snackBar.open(
          this.isEditMode() ? 'Produkt aktualisiert' : 'Produkt erstellt',
          'OK',
          { duration: 2000 }
        );
        this.router.navigate(['/dashboard/products']);
      },
      error: () => {
        this.snackBar.open('Fehler beim Speichern', 'OK', { duration: 3000 });
        this.isLoading.set(false);
      }
    });
  }

  formatPrice(price: string): string {
    const num = parseFloat(price);
    if (isNaN(num)) return '0,00 €';
    return new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' }).format(num);
  }

  calculateGross(): string {
    const net = parseFloat(this.form.get('unit_price')?.value) || 0;
    const vatRate = parseFloat(this.form.get('vat_rate')?.value) || 0;
    const gross = net * (1 + vatRate / 100);
    return this.formatPrice(gross.toString());
  }
}
