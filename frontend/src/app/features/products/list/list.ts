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
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { ApiService, Product } from '../../../core/services/api';

@Component({
  selector: 'app-product-list',
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
    MatSnackBarModule
  ],
  templateUrl: './list.html',
  styleUrl: './list.scss'
})
export class ListComponent implements OnInit {
  products = signal<Product[]>([]);
  isLoading = signal(true);
  displayedColumns = ['sku', 'name', 'unit_price', 'vat_rate', 'status', 'actions'];

  constructor(
    private apiService: ApiService,
    private snackBar: MatSnackBar
  ) {}

  ngOnInit(): void {
    this.loadProducts();
  }

  loadProducts(): void {
    this.isLoading.set(true);
    this.apiService.getProducts().subscribe({
      next: (data: any) => {
        const products = Array.isArray(data) ? data : (data.results || []);
        this.products.set(products);
        this.isLoading.set(false);
      },
      error: () => {
        this.snackBar.open('Fehler beim Laden der Produkte', 'OK', { duration: 3000 });
        this.products.set([]);
        this.isLoading.set(false);
      }
    });
  }

  onSearch(event: Event): void {
    const value = (event.target as HTMLInputElement).value;
    this.apiService.getProducts({ search: value }).subscribe({
      next: (data: any) => {
        const products = Array.isArray(data) ? data : (data.results || []);
        this.products.set(products);
      }
    });
  }

  deleteProduct(id: number): void {
    if (confirm('Produkt wirklich löschen?')) {
      this.apiService.deleteProduct(id).subscribe({
        next: () => {
          this.products.update(list => list.filter(p => p.id !== id));
          this.snackBar.open('Produkt gelöscht', 'OK', { duration: 2000 });
        },
        error: () => {
          this.snackBar.open('Fehler beim Löschen', 'OK', { duration: 3000 });
        }
      });
    }
  }

  formatPrice(price: string): string {
    return new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' }).format(parseFloat(price));
  }
}
