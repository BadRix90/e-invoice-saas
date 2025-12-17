import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { MatTableModule } from '@angular/material/table';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { ApiService, Customer } from '../../../core/services/api';

@Component({
  selector: 'app-customer-list',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    MatTableModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatInputModule,
    MatFormFieldModule,
    MatSnackBarModule
  ],
  templateUrl: './list.html',
  styleUrl: './list.scss'
})
export class ListComponent implements OnInit {
  customers = signal<Customer[]>([]);
  isLoading = signal(true);
  displayedColumns = ['customer_number', 'display_name', 'city', 'email', 'actions'];

  constructor(
    private apiService: ApiService,
    private snackBar: MatSnackBar
  ) {}

  ngOnInit(): void {
    this.loadCustomers();
  }

  loadCustomers(): void {
    this.isLoading.set(true);
    this.apiService.getCustomers().subscribe({
      next: (data) => {
        this.customers.set(data);
        this.isLoading.set(false);
      },
      error: (err) => {
        this.snackBar.open('Fehler beim Laden der Kunden', 'OK', { duration: 3000 });
        this.isLoading.set(false);
      }
    });
  }

  onSearch(event: Event): void {
    const value = (event.target as HTMLInputElement).value;
    this.apiService.getCustomers({ search: value }).subscribe({
      next: (data) => this.customers.set(data)
    });
  }

  deleteCustomer(id: number): void {
    if (confirm('Kunde wirklich löschen?')) {
      this.apiService.deleteCustomer(id).subscribe({
        next: () => {
          this.customers.update(list => list.filter(c => c.id !== id));
          this.snackBar.open('Kunde gelöscht', 'OK', { duration: 2000 });
        },
        error: () => {
          this.snackBar.open('Fehler beim Löschen', 'OK', { duration: 3000 });
        }
      });
    }
  }
}
