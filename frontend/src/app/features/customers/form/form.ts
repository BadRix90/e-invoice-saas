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
import { MatDividerModule } from '@angular/material/divider';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { ApiService, Customer } from '../../../core/services/api';

@Component({
  selector: 'app-customer-form',
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
  customerId: number | null = null;

  constructor(
    private fb: FormBuilder,
    private apiService: ApiService,
    private router: Router,
    private route: ActivatedRoute,
    private snackBar: MatSnackBar
  ) {
    this.form = this.fb.group({
      is_business: [true],
      company_name: [''],
      first_name: [''],
      last_name: [''],
      street: ['', Validators.required],
      zip_code: ['', Validators.required],
      city: ['', Validators.required],
      country: ['DE', Validators.required],
      email: ['', [Validators.email]],
      phone: [''],
      vat_id: [''],
      leitweg_id: [''],
      payment_terms_days: [30, [Validators.required, Validators.min(0)]]
    });
  }

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (id && id !== 'new') {
      this.customerId = parseInt(id, 10);
      this.isEditMode.set(true);
      this.loadCustomer();
    }
  }

  loadCustomer(): void {
    if (!this.customerId) return;
    this.isLoading.set(true);
    this.apiService.getCustomer(this.customerId).subscribe({
      next: (customer) => {
        this.form.patchValue(customer);
        this.isLoading.set(false);
      },
      error: () => {
        this.snackBar.open('Fehler beim Laden', 'OK', { duration: 3000 });
        this.router.navigate(['/dashboard/customers']);
      }
    });
  }

  onSubmit(): void {
    if (this.form.invalid) return;

    this.isLoading.set(true);
    const data = this.form.value;

    const request = this.isEditMode()
      ? this.apiService.updateCustomer(this.customerId!, data)
      : this.apiService.createCustomer(data);

    request.subscribe({
      next: () => {
        this.snackBar.open(
          this.isEditMode() ? 'Kunde aktualisiert' : 'Kunde erstellt',
          'OK',
          { duration: 2000 }
        );
        this.router.navigate(['/dashboard/customers']);
      },
      error: () => {
        this.snackBar.open('Fehler beim Speichern', 'OK', { duration: 3000 });
        this.isLoading.set(false);
      }
    });
  }
}
