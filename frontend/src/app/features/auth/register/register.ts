import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { AuthService } from '../../../core/services/auth';

@Component({
  selector: 'app-register',
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
    MatProgressSpinnerModule,
    MatSnackBarModule
  ],
  templateUrl: './register.html',
  styleUrl: './register.scss'
})
export class Register {
  registerForm: FormGroup;
  isLoading = signal(false);
  hidePassword = signal(true);
  hidePassword2 = signal(true);
  errorMessage = signal<string | null>(null);
  successMessage = signal<string | null>(null);
  isNewCompany = signal(false);

  constructor(
    private fb: FormBuilder,
    private authService: AuthService,
    private router: Router,
    private snackBar: MatSnackBar
  ) {
    this.registerForm = this.fb.group({
      username: ['', Validators.required],
      email: ['', [Validators.required, Validators.email]],
      first_name: [''],
      last_name: [''],
      password: ['', [Validators.required, Validators.minLength(8)]],
      password2: ['', Validators.required],
      company_code: ['', Validators.required],
      company_name: ['']
    });

    this.registerForm.get('company_code')?.valueChanges.subscribe(() => {
      this.checkCompanyCode();
    });
  }

  checkCompanyCode(): void {
    const code = this.registerForm.get('company_code')?.value;
    if (code && code.length >= 5) {
      this.authService.checkCompanyCode(code).subscribe({
        next: (exists) => {
          this.isNewCompany.set(!exists);
          if (!exists) {
            this.registerForm.get('company_name')?.setValidators(Validators.required);
          } else {
            this.registerForm.get('company_name')?.clearValidators();
          }
          this.registerForm.get('company_name')?.updateValueAndValidity();
        }
      });
    }
  }

  onSubmit(): void {
    if (this.registerForm.invalid) return;

    const password = this.registerForm.get('password')?.value;
    const password2 = this.registerForm.get('password2')?.value;

    if (password !== password2) {
      this.snackBar.open('Passwörter stimmen nicht überein', 'Schließen', {
        duration: 5000,
        panelClass: ['error-snackbar']
      });
      return;
    }

    this.isLoading.set(true);
    this.errorMessage.set(null);

    this.authService.register(this.registerForm.value).subscribe({
      next: () => {
        this.snackBar.open('Registrierung erfolgreich! Sie werden weitergeleitet...', 'OK', {
          duration: 3000,
          panelClass: ['success-snackbar']
        });
        setTimeout(() => {
          this.router.navigate(['/auth/login']);
        }, 2000);
      },
      error: (err) => {
        this.isLoading.set(false);

        let errorMsg = 'Registrierung fehlgeschlagen';

        if (err.error?.password) {
          errorMsg = err.error.password[0];
        } else if (err.error?.username) {
          errorMsg = 'Benutzername: ' + err.error.username[0];
        } else if (err.error?.email) {
          errorMsg = 'E-Mail: ' + err.error.email[0];
        } else if (err.error?.company_name) {
          errorMsg = err.error.company_name[0];
        }

        this.snackBar.open(errorMsg, 'Schließen', {
          duration: 8000,
          panelClass: ['error-snackbar']
        });
      }
    });
  }
}
