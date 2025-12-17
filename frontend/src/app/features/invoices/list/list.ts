import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { MatTableModule } from '@angular/material/table';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatChipsModule } from '@angular/material/chips';
import { MatMenuModule } from '@angular/material/menu';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { ApiService, Invoice } from '../../../core/services/api';

@Component({
  selector: 'app-invoice-list',
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
    MatChipsModule,
    MatMenuModule,
    MatSnackBarModule
  ],
  templateUrl: './list.html',
  styleUrl: './list.scss'
})
export class ListComponent implements OnInit {
  invoices = signal<Invoice[]>([]);
  isLoading = signal(true);
  displayedColumns = ['invoice_number', 'customer_name', 'invoice_date', 'total', 'status', 'format', 'actions'];

  constructor(
    private apiService: ApiService,
    private snackBar: MatSnackBar
  ) {}

  ngOnInit(): void {
    this.loadInvoices();
  }

  loadInvoices(): void {
    this.isLoading.set(true);
    this.apiService.getInvoices().subscribe({
      next: (data) => {
        this.invoices.set(data);
        this.isLoading.set(false);
      },
      error: () => {
        this.snackBar.open('Fehler beim Laden der Rechnungen', 'OK', { duration: 3000 });
        this.isLoading.set(false);
      }
    });
  }

  onSearch(event: Event): void {
    const value = (event.target as HTMLInputElement).value;
    this.apiService.getInvoices({ search: value }).subscribe({
      next: (data) => this.invoices.set(data)
    });
  }

  formatPrice(price: string): string {
    return new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' }).format(parseFloat(price));
  }

  formatDate(date: string): string {
    return new Date(date).toLocaleDateString('de-DE');
  }

  getStatusClass(status: string): string {
    return `status-${status}`;
  }

  deleteInvoice(id: number): void {
    if (confirm('Rechnung wirklich löschen?')) {
      this.apiService.deleteInvoice(id).subscribe({
        next: () => {
          this.invoices.update(list => list.filter(i => i.id !== id));
          this.snackBar.open('Rechnung gelöscht', 'OK', { duration: 2000 });
        },
        error: () => {
          this.snackBar.open('Fehler beim Löschen', 'OK', { duration: 3000 });
        }
      });
    }
  }

  duplicateInvoice(id: number): void {
    this.apiService.duplicateInvoice(id).subscribe({
      next: (newInvoice) => {
        this.invoices.update(list => [newInvoice, ...list]);
        this.snackBar.open('Rechnung dupliziert', 'OK', { duration: 2000 });
      },
      error: () => {
        this.snackBar.open('Fehler beim Duplizieren', 'OK', { duration: 3000 });
      }
    });
  }

  downloadPdf(id: number): void {
    // TODO: Implementieren wenn PDF-Generierung fertig
    this.snackBar.open('PDF-Download kommt bald', 'OK', { duration: 2000 });
  }

  downloadXml(id: number): void {
    // TODO: Implementieren wenn XML-Generierung fertig
    this.snackBar.open('XML-Download kommt bald', 'OK', { duration: 2000 });
  }
}
