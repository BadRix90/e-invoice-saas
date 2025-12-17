import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatIconModule } from '@angular/material/icon';
import { MatTabsModule } from '@angular/material/tabs';
import { ApiService } from '../../core/services/api';

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatCardModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatSnackBarModule,
    MatIconModule,
    MatTabsModule,
  ],
  templateUrl: './settings.html',
  styleUrl: './settings.scss'
})
export class SettingsComponent implements OnInit {
  form: FormGroup;
  loading = signal(false);
  saving = signal(false);

  constructor(
    private fb: FormBuilder,
    private apiService: ApiService,
    private snackBar: MatSnackBar
  ) {
    this.form = this.fb.group({
      name: ['', Validators.required],
      company_name: [''],
      street: ['', Validators.required],
      zip_code: ['', Validators.required],
      city: ['', Validators.required],
      country: ['DE', Validators.required],
      tax_id: [''],
      vat_id: [''],
      email: ['', [Validators.required, Validators.email]],
      phone: [''],
      bank_name: [''],
      iban: [''],
      bic: [''],
    });
  }

  ngOnInit(): void {
    this.loadSettings();
  }

  loadSettings(): void {
    this.loading.set(true);
    this.apiService.getTenant().subscribe({
      next: (tenant) => {
        this.form.patchValue(tenant);
        this.loading.set(false);
      },
      error: () => {
        this.snackBar.open('Fehler beim Laden', 'OK', { duration: 3000 });
        this.loading.set(false);
      }
    });
  }

  save(): void {
    if (this.form.invalid) {
      this.snackBar.open('Bitte alle Pflichtfelder ausfüllen', 'OK', { duration: 3000 });
      return;
    }

    this.saving.set(true);
    this.apiService.updateTenant(this.form.value).subscribe({
      next: () => {
        this.snackBar.open('Einstellungen gespeichert', 'OK', { duration: 2000 });
        this.saving.set(false);
      },
      error: () => {
        this.snackBar.open('Fehler beim Speichern', 'OK', { duration: 3000 });
        this.saving.set(false);
      }
    });
  }
}
